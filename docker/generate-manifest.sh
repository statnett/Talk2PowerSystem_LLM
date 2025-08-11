set -ex

rm -f git-manifest.yaml

cat > git-manifest.yaml <<EOF
Git-SHA: '$(git rev-parse HEAD)'
Build-Branch: '$(git branch --show-current)'
Build-Timestamp: '$(date +"%Y-%m-%dT%H:%M:%SZ")'
EOF
