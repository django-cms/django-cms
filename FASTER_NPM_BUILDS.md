To speed up local building of npm dependencies run

```
docker-compose run --rm web /app/cache_node_modules.sh
```

after each rebuild of the image.

So from now on, instead of:

```
docker-compose build web
```

Do

```
docker-compose build web && docker-compose run --rm web /app/cache_node_modules.sh
```


The first build will still be slow. But all following builds will be
faster.
To drop the cache delete ``.cache.node_modules.tar.gz`` and rebuild.

