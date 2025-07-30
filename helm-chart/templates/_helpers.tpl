{{/*
Combined image pull secrets
*/}}
{{- define "t2ps-chatbot-llm.combinedImagePullSecrets" -}}
  {{- $secrets := concat .Values.global.imagePullSecrets .Values.image.pullSecrets }}
  {{- tpl (toYaml $secrets) . -}}
{{- end -}}

{{/*
Renders the container image for t2ps-chatbot-llm
*/}}
{{- define "t2ps-chatbot-llm.image" -}}
  {{- $repository := .Values.image.repository -}}
  {{- $tag := .Values.image.tag | default .Chart.AppVersion | toString -}}
  {{- $image := printf "%s:%s" $repository $tag -}}
  {{/* Add registry if present */}}
  {{- $registry := .Values.global.imageRegistry | default .Values.image.registry -}}
  {{- if $registry -}}
    {{- $image = printf "%s/%s" $registry $image -}}
  {{- end -}}
  {{/* Add SHA digest if provided */}}
  {{- if .Values.image.digest -}}
    {{- $image = printf "%s@%s" $image .Values.image.digest -}}
  {{- end -}}
  {{- $image -}}
{{- end -}}

{{/*
Renders the internal host of the Redis instance.
*/}}
{{- define "redis.host" -}}
  {{- if .Values.redis.enabled -}}
    {{ printf "%s-master" (include "common.names.fullname" $.Subcharts.redis)}}
  {{- end -}}
{{- end -}}
