FROM node:20.11.1-alpine3.19 as builder

WORKDIR /root

RUN apk add --no-cache git \
    && git clone https://github.com/lichifeng/MgxParser.git

WORKDIR /root/MgxParser

RUN apk add --no-cache \
    alpine-sdk \
    cmake \
    libpng-dev openssl-dev
RUN npm install
RUN npx cmake-js rebuild --CDBUILD_STATIC=OFF -p $(nproc)


FROM python:alpine3.19

WORKDIR /mgxhub

COPY . .
COPY --from=builder /root/MgxParser/build/Release/MgxParser_D_EXE /mgxhub/mgxhub/parser/
COPY --from=builder /root/MgxParser/build/Release/libMgxParser_SHARED.so /mgxhub/mgxhub/parser/

RUN apk update && apk add --no-cache libpng openssl libstdc++ libgcc

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]