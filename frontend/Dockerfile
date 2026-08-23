FROM node:20
WORKDIR /app

COPY package.json package.json
COPY package-lock.json package-lock.json

RUN npm install --legacy-peer-deps

COPY . .
ENV CI=false
ENV DISABLE_ESLINT_PLUGIN=true
RUN npm run build

CMD ["npx", "-y", "http-server", "-p", "8000", "/app/build"]
