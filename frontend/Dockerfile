# Production-ready multi-stage build for the React frontend
# Build stage
FROM node:18-alpine as build
WORKDIR /app

# Allow injecting the API base at build time, with a fallback to the local nginx proxy path
ARG REACT_APP_API_BASE=/api
ENV REACT_APP_API_BASE=${REACT_APP_API_BASE}

COPY frontend/package.json ./package.json
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/.env* ./
RUN npm install --no-audit --no-fund
RUN npm run build

# Production stage - serve with nginx
FROM nginx:stable-alpine as prod
COPY --from=build /app/build /usr/share/nginx/html
RUN rm /etc/nginx/conf.d/default.conf
COPY frontend/nginx.conf /etc/nginx/conf.d/insightq.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
