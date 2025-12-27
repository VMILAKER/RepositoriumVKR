FROM node:latest AS builder

WORKDIR /Frontend

ENV PATH ./node_modules/.bin:$PATH
COPY package*.json .

RUN npm install --silent

COPY . .
RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "dev"]

