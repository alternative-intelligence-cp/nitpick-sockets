# `tools/` — generators and instruments

`fuzz_addr.py` (the address parsers) and `fuzz_cmsg.py` (the `cmsghdr` reader).
Anything a generator emits is committed as source and checked by regeneration.
