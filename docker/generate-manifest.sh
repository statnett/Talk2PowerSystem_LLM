set -ex

rm -f git-manifest.yaml

BRANCH=$(echo "${GITHUB_REF_NAME:-${GITHUB_HEAD_REF}}")
if [ -z "$BRANCH" ]; then
  BRANCH=$(git branch --show-current)
fi

cat > git-manifest.yaml <<EOF
Git-SHA: '$(git rev-parse HEAD)'
Build-Branch: '${BRANCH}'
Build-Timestamp: '$(date +"%Y-%m-%dT%H:%M:%SZ")'
EOF
