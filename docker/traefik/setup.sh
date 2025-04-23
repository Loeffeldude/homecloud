cp .env.example .env

if [ ! -e "acme.json" ]; then
  echo "{}" > acme.json
fi

# create the external network
# TODO move web network to not external
docker network ls | grep "web" || docker network create web
