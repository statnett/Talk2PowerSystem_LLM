import os

os.environ["UNSLOTH_VLLM_STANDBY"] = "1"
import unsloth
import json
import logging
from langgraph.checkpoint.memory import MemorySaver

import time
from tqdm import tqdm
from typing import Any
import uuid
import torch
import logging
import os
import fire
from datasets import Dataset
import weave
import art
from art.local import LocalBackend
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from graphrag_eval.steps.sparql import compare_sparql_results

from tenacity import retry, stop_after_attempt

from agent_hf import Talk2PowerSystemAgent
from art.langgraph import wrap_rollout

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Response(BaseModel):
    response: bool


RESPONSE_EVAL_PROMPT = """You are an impartial, strict expert evaluator acting as a reward model for an LLM training pipeline.

Your task is to evaluate a "Model Generated Answer" based on a specific "User Question". You must determine if the answer meets the acceptance criteria.

You must output your decision as a structured JSON object.

### Acceptance Criteria
To receive a valid response (True), the answer must satisfy ALL of the following conditions:

1.  **Strict Language Purity (CRITICAL):**
    * The answer must be written **100% in English**.
    * There must be NO language mixing or unexpected characters from other scripts (e.g., Chinese, Cyrillic, Arabic).
    * If the answer drifts into another language halfway through, or ends with a non-English sentence, it is a FAIL.

2.  **Relevance:**
    * The answer must address the premise of the User Question.
    * It must not be a refusal or a generic hallucination unrelated to the prompt.
    * If the answer mentions tool calls or SPARQL QUERIES USED that is acceptable.

3.  **Formatting & Structure:**
    * The answer must be well-structured (e.g., proper use of paragraphs, Markdown where appropriate).
    * It must not contain raw internal tokens (like `<|endoftext|>`) or broken encoding.

### Evaluation Logic
If the answer violates *any* of the criteria above (especially Language Purity), the `response` is `False`.
If the answer meets *all* criteria, the `response` is `True`.

### Output Format
You must respond strictly with a JSON object adhering to this schema:
{{
  "response": boolean
}}

Question:
{question}

Answer:
{answer}

"""


class StreamingAverage:
    def __init__(self):
        self.avg = 0.0
        self.count = 0

    def update(self, new_value):
        self.count += 1
        # Update the average incrementally
        self.avg = self.avg + (new_value - self.avg) / self.count
        return self.avg


stream = StreamingAverage()
stream_scaled = StreamingAverage()
stream_time = StreamingAverage()


@weave.op()
async def rollout(
    model: art.Model,
    question: str,
    sparql_step_output: Any,
    required_columns: list[str],
    client=None,
    base_model=None,
    max_time=200,
    path_to_yaml_config="dev_open_models_no_ontology.yaml",
    q2subset: dict[str, str] | None = None,
) -> art.Trajectory:
    checkpointer = MemorySaver()
    system = Talk2PowerSystemAgent(
        model=model,
        path_to_yaml_config=path_to_yaml_config,
        checkpointer=checkpointer,
    )
    traj = art.Trajectory(
        reward=0.0,
        messages_and_choices=[],
        metadata={},
    )
    agent = system.agent
    tik = time.time()
    try:
        # Run the agent
        config = {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 25,
        }
        try:
            instructions = system.instructions
            if q2subset is not None:
                if question in q2subset:
                    subset = q2subset[question]
                    instructions = instructions.replace("{ontology_schema}", subset)
                else:
                    print("Error No ontology subset for question: ", question)
            result = await agent.ainvoke(
                {
                    "messages": [
                        SystemMessage(content=instructions),
                        HumanMessage(
                            content=question,
                        ),
                    ]
                },
                config=config,
            )
        except Exception as agent_exception:
            print("Agent_exception", agent_exception)
            messages = checkpointer.get(config)["channel_values"]["messages"][:-1]
            result = {}
            result["messages"] = messages

        reward = 0
        with open("full_trace.jsonl", "w", encoding="utf-8") as f:
            serializable_state = {
                "messages": [m.model_dump() for m in result["messages"]]
            }
            f.write(json.dumps(serializable_state) + "\n")
            f.flush()
        tok = time.time()
        total_time = tok - tik
        for el in result["messages"]:
            if isinstance(el, ToolMessage):
                try:
                    reward = max(
                        reward,
                        compare_sparql_results(
                            json.loads(sparql_step_output),
                            json.loads(el.content),
                            required_columns,
                        ),
                    )
                except:
                    pass
        if client and reward > 0:
            try:
                response = await client.chat.completions.parse(
                    temperature=0,
                    model=base_model,
                    messages=[
                        {
                            "role": "system",
                            "content": RESPONSE_EVAL_PROMPT.format(
                                question=question, answer=result["messages"][-1].content
                            ),
                        },
                    ],
                    max_completion_tokens=1000,
                    response_format=Response,
                )
                result = response.choices[0].message.parsed.model_dump()["response"]
                if not result:
                    print("Bad response")
                    reward = 0
            except Exception as e:
                print("Failed answer evaluation", e)
                print(result["messages"][-1])

        print("Average: ", stream.update(reward))
        print("Reward: ", reward)
        reward /= total_time
        if total_time > max_time:
            reward = 0
        print("Average time: ", stream_time.update(total_time))
        print("Time: ", total_time)
        print("Average scaled: ", stream_scaled.update(reward))
        print("Reward scaled: ", reward)
        traj.reward = reward

    except Exception as e:
        print(f"Error running LangGraph agent: {e}")
        # Add error information to trajectory
        traj.messages_and_choices.append(
            {"role": "assistant", "content": f"Error: {str(e)}"}
        )
    print(traj)
    return traj


async def main(
    name=None,
    max_tokens=20000,  # 22528
    train="train_rl.json",
    gpu_memory_utilization=0.70,
    r=16,
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_alpha=16,
    use_gradient_checkpointing="unsloth",
    run_name="",
    beta=0.01,
    adam_beta1=0.9,
    adam_beta2=0.99,
    learning_rate=5e-7,
    lr_scheduler_type="constant",
    optim="paged_adamw_8bit",
    weight_decay=0.1,
    max_grad_norm=0.2,
    subsets=None,
    groups_per_step=1,
    num_epochs=1,
    rollouts_per_group=8,
    max_time=200,
    path_to_yaml_config="dev_open_models_no_ontology.yaml",
    **kwargs,
):
    print(subsets)
    if subsets is not None:
        with open(subsets, "r", encoding="utf-8") as f:
            q2subset = json.load(f)
        print("Loaded subsets")
    else:
        q2subset = None
    model_name = kwargs["model_name"]
    print("Model name ", model_name)
    train = Dataset.from_json(train)
    print("train_dataset", train)
    model = art.TrainableModel(
        name=name,
        trust_remote_code=True,
        project="statnett",
        base_model=model_name,
        _internal_config=art.dev.InternalModelConfig(
            init_args=art.dev.InitArgs(
                trust_remote_code=True,
                max_seq_length=max_tokens,
            ),
            engine_args=art.dev.EngineArgs(
                gpu_memory_utilization=gpu_memory_utilization,
                max_model_len=max_tokens,
            ),
            peft_args=art.dev.PeftArgs(
                lora_alpha=lora_alpha,
                r=r,
                target_modules=target_modules,
                use_gradient_checkpointing=use_gradient_checkpointing,
            ),
            trainer_args=art.dev.TrainerArgs(
                beta=beta,
                adam_beta1=adam_beta1,
                adam_beta2=adam_beta2,
                learning_rate=learning_rate,
                lr_scheduler_type=lr_scheduler_type,
                max_grad_norm=max_grad_norm,
                optim=optim,
                weight_decay=weight_decay,
            ),
        ),
    )
    backend = LocalBackend(
        path="./.art",
    )

    await model.register(backend)
    client = model.openai_client()

    from art.utils import iterate_dataset

    training_config = {
        "groups_per_step": groups_per_step,
        "num_epochs": num_epochs,
        "rollouts_per_group": rollouts_per_group,
        "learning_rate": learning_rate,
    }

    # Use iterate_dataset with real training scenarios (similar to train.py)
    training_iterator = iterate_dataset(
        train,  # Use real scenarios from Hugging Face
        groups_per_step=training_config["groups_per_step"],
        num_epochs=training_config["num_epochs"],
        initial_step=await model.get_step(),
    )

    for batch in tqdm(training_iterator, desc="Processing training_iterator"):
        print(
            f"Training step {batch.step}, epoch {batch.epoch}, epoch step {batch.epoch_step}"
        )
        print(f"Batch contains {len(batch.items)} scenarios")

        # Create trajectory groups for this batch (similar to train.py)
        groups = []
        for items in batch.items:
            groups.append(
                art.TrajectoryGroup(
                    (
                        wrap_rollout(model, rollout)(
                            model,
                            items["question_text"],
                            items["sparql_step_output"],
                            items["required_columns"],
                            client,
                            model_name,
                            max_time,
                            path_to_yaml_config,
                            q2subset,
                        )
                        for _ in range(training_config["rollouts_per_group"])
                    )
                )
            )

        # Gather all trajectory groups
        finished_groups = await art.gather_trajectory_groups(
            groups,
            pbar_desc="gather",
            max_exceptions=training_config["rollouts_per_group"] * len(batch.items),
        )

        # await model.delete_checkpoints()
        await model.train(
            finished_groups,
            config=art.TrainConfig(
                learning_rate=training_config["learning_rate"],
                importance_sampling_level="sequence",
            ),
            # Lowering the logprob_calculation_chunk_size is a memory saving measure
            _config={"logprob_calculation_chunk_size": 8},
        )


if __name__ == "__main__":
    fire.Fire(main)
