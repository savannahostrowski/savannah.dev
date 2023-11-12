FROM klakegg/hugo:0.101.0-onbuild AS hugo

FROM nginx
COPY --from=hugo /public /usr/share/nginx/html