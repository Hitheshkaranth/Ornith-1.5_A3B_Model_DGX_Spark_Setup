# Derived from the NVIDIA vLLM image to fix tool-calling on 26.07.
# The base pins xgrammar==0.2.0, but this vLLM build imports
# xgrammar.normalize_tool_choice, which only exists in xgrammar>=0.2.4.
# Any chat request with `tools` 500s without this. --no-deps keeps the
# container's transformers 5.6.1 (and everything else) untouched.
FROM nvcr.io/nvidia/vllm:26.07-py3

RUN pip install --no-cache-dir --no-deps xgrammar==0.2.4
