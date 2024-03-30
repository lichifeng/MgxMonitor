FROM node:lts-bookworm-slim as builder

WORKDIR /root

RUN apt-get update && apt-get install -y git \
    && git clone https://github.com/lichifeng/MgxParser.git

WORKDIR /root/MgxParser

RUN apt-get install -y \
    build-essential \
    cmake \
    libpng-dev libssl-dev
RUN npm install
RUN npx cmake-js rebuild --CDBUILD_STATIC=OFF -p $(nproc)


FROM python:3.12.2-slim-bookworm

WORKDIR /mgxhub

COPY . .
COPY --from=builder /root/MgxParser/build/Release/MgxParser_D_EXE /mgxhub/mgxhub/parser/
COPY --from=builder /root/MgxParser/build/Release/libMgxParser_SHARED.so /mgxhub/mgxhub/parser/

RUN <<EOF 
echo "deb http://deb.debian.org/debian bookworm main non-free" > /etc/apt/sources.list
apt-get update
apt-get update --allow-releaseinfo-change
apt-get install -y libpng16-16 openssl p7zip-full unrar
pip install --no-cache-dir -r requirements.txt
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]