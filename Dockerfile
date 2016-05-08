FROM ubuntu:14:04
MAINTAINER jemromerol@gmail.com

VOLUME ["/opt/apasvo"]

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y git python-pip \
    && conda install apasvo
 
