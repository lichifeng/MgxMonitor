FROM python:slim as builder

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake git curl \
    libpng-dev libssl-dev
RUN curl -fsSL https://deb.nodesource.com/setup_21.x | bash - 
RUN apt-get install -y nodejs
RUN git clone https://github.com/lichifeng/MgxParser.git
WORKDIR /MgxParser
RUN cd /MgxParser
RUN npm install
RUN npx cmake-js rebuild -p $(nproc)


FROM python:slim

WORKDIR /mgxhub

COPY . .
COPY --from=builder /MgxParser/build/MgxParser_D_EXE /mgxhub/mgxhub/parser/
COPY --from=builder /MgxParser/build/Release/libMgxParser_SHARED.so /mgxhub/mgxhub/parser/

RUN apt-get update && apt-get install -y libpng16-16 openssl curl

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]