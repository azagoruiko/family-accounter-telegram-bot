DOCKER_REPO="10.8.0.1:9999/docker"
VER=0.0.1
export NOMAD_ADDR="http://127.0.0.1:4646"
if [ ! -e $1 ]; then
    VER=$1
fi
export VER
echo $VER
DOCKER_TAG="${DOCKER_REPO}/accounter-bot:${VER}"
echo $DOCKER_TAG

docker build -t "$DOCKER_TAG"  .
docker push "$DOCKER_TAG"

nomad job run accounter_bot.nomad
