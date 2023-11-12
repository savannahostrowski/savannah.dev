FROM klakegg/hugo:0.101.0-onbuild AS hugo

FROM nginx
COPY --from=hugo /target /usr/share/nginx/html