#!/usr/bin/env bash

. path.sh

export CUDA_VISIBLE_DEVICES=""

# See
# https://huggingface.co/ptrnull/icefall-asr-conv-emformer-transducer-stateless2-zh
dir=./icefall-asr-conv-emformer-transducer-stateless2-zh
if [ ! -f $dir/exp/epoch-99.pt ]; then
  pushd $dir/exp
  ln -sv pretrained-epoch-11-avg-1.pt epoch-99.pt
  popd
fi

./conv_emformer_transducer_stateless2/export-for-ncnn.py \
  --exp-dir $dir/exp \
  --lang-dir $dir/data/lang_char_bpe \
  --epoch 99 \
  --avg 1 \
  --use-averaged-model 0 \
  \
  --num-encoder-layers 12 \
  --chunk-length 32 \
  --cnn-module-kernel 31 \
  --left-context-length 32 \
  --right-context-length 8 \
  --memory-size 32

pushd $dir/exp
pnnx ./encoder_jit_trace-pnnx.pt
pnnx ./decoder_jit_trace-pnnx.pt
pnnx ./joiner_jit_trace-pnnx.pt
