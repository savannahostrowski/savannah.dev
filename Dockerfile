FROM klakegg/hugo:0.101.0-onbuild AS hugo

COPY / /src

RUN hugo --source=/src --destination=/public

FROM nginx
COPY --from=hugo /public /usr/share/nginx/html