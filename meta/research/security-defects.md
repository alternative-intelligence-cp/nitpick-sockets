# Published defects in the reference implementations' socket parse and decode paths — research digest

**As of 2026-10-29.** Question: which published defects — CVEs and upstream bug records — have the reference implementations of the BSD socket surface this library re-implements had, in the five places it parses or decodes: IPv4 and IPv6 text addresses (glibc and musl `inet_pton`/`inet_aton`, Python `ipaddress`, Go `net/netip`, Rust `std::net`), `sockaddr_un` paths, `cmsghdr` walks (`CMSG_NXTHDR`), `SCM_RIGHTS` descriptor passing, and `SO_PEERCRED`/`SCM_CREDENTIALS` identity? Request 1 of 3, nitpick-sockets 0.0.0 plan §13 at af50100. Sensitivity is security, so this digest is stale ninety days after its date, on 2027-01-27.

## Answer

Published defects exist in all five places. There are CVEs for text addresses (Python, Go, Rust, musl), for an overlong `sockaddr_un` path copy (glibc) and for credential passing (Linux kernel). For the `cmsghdr` walk and for `SCM_RIGHTS` there are upstream bug records and no CVE found.

- **Text addresses.** A leading zero in an IPv4 octet that other software reads as octal is CVE-2021-29921 (Python `ipaddress`; fix merged 2021-05-02), CVE-2021-29923 (Go `net.ParseIP`/`ParseCIDR`; fixed in Go 1.17) and CVE-2021-29922 (Rust `std::net`; fixed in 1.53.0, NVD only). Go's new `net/netip` parser re-opened the same hole during the Go 1.18 cycle and was fixed within a day (golang/go#49365, no CVE).
- **musl `inet_pton`.** It had a stack buffer overflow (CVE-2015-1817; fix commit 2015-03-23). It also had an uninitialised-memory read on IPv4-mapped IPv6 input (fix 2023-02-12, no CVE found). NVD's keyword search found no glibc `inet_pton` CVE; `inet_aton` was not searched.
- **`sockaddr_un`.** glibc CVE-2022-23218 is an unchecked copy of an overlong path into `sun_path`. It sits in a legacy sunrpc call; the class is the copy.
- **`cmsghdr` walk.** Three records: glibc BZ 28846 (pointer advanced before the bounds check); a December 2025 musl report that `CMSG_NXTHDR` returns NULL for a final empty-payload header ending exactly at the buffer end; and the kernel's own `msg_controllen` underflow in `scm_detach_fds` on the `SCM_RIGHTS` receive side, when an odd number of descriptors leaves out 4 bytes of tail padding.
- **Credentials.** Kernel CVE-2013-1979 (`scm_set_cred` used incorrect uid and gid values). Nothing was read on `SO_PEERCRED` as such.

Only the Python and Go leading-zero CVEs reached two independent primaries. Everything else rests on one primary (1P) or is an unread lead (last section).

## Evidence

- https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=zero+characters+IP+address&resultsPerPage=20 — retrieved 2026-10-29 — (paraphrase; the fetch tool would not quote over 125 characters) totalResults 11, none tagged disputed. CVE-2021-29921: Python before 3.9.5 `ipaddress` mishandles leading zeros in IP octets (published 2021-05-06). CVE-2021-29922: Rust before 1.53.0 `std::net` parser, unexpected octal interpretation (2021-08-07). CVE-2021-29923: Go before 1.17 `net.ParseIP` and `net.ParseCIDR` (2021-08-07). The same class is in Django CVE-2021-33571 and in Perl modules (CVE-2021-29662, -29424, -47154, -47155, -47156, and CVE-2025-40910 and CVE-2025-40911, the last two for CIDR strings).
- https://github.com/python/cpython/pull/25099 — retrieved 2026-10-29 — "Like socket.inet_pton() any leading zero is now treated as invalid input." The PR is titled "bpo-36384: Leading zeros in IPv4 addresses are no longer tolerated". It was merged 2021-05-02 as 60ce8f0, carries the label type-security, and says "Reverts commit e653d4d8e820a7a004ad399530af0135b45db27a and makes parsing even more strict." Backports are GH-25815 for 3.9 and GH-27801 for 3.8. A core developer's comment calls it not "our vulnerability, but an inconsistency with other vulnerable libraries".
- https://github.com/golang/go/issues/49365 — retrieved 2026-10-29 — "netip.ParseAddr reintroduces the behavior we removed from net.ParseIP." The issue is titled "net/netip: IPv4 parser accepts leading zeroes", labelled Security and release-blocker, milestone Go1.18. It was opened 2021-11-04 and closed 2021-11-05 by commit 3796df1 (CL 361534, "net/netip: don't accept ParseAddr with leading zeros"). It says Go 1.17 "took a backwards compatibility hit to reject IPv4 addresses with leading zeroes in net.ParseIP" because such addresses "can be parsed differently (as octal) by the operating system". No CVE is named. IPv4-in-IPv6 text and ParsePrefix are not discussed.
- https://git.musl-libc.org/cgit/musl/log/src/network/inet_pton.c — retrieved 2026-10-29 — "fix internal buffer overrun in inet_pton" (2015-03-23, Rich Felker, fc13acc3). The log also has "inet_pton: fix uninitialized memory use for IPv4-mapped IPv6 addresses" (2023-02-12, Alexey Izbyshev, 7e13e5ae). It has the lone-"::" fix (2011-04-25, 3486365e) and two return-value fixes (2011-04-21, 31f014e0; 2013-10-19, 38b9c027). The log names no CVE.
- https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=inet_pton&resultsPerPage=60 — retrieved 2026-10-29 — "Stack-based buffer overflow in the inet_pton function in network/inet_pton.c in musl libc" (excerpt). This is CVE-2015-1817, published 2017-08-18, status Modified; its reference list includes http://www.openwall.com/lists/oss-security/2015/03/30/3, not opened. totalResults is 4. The others are CVE-2021-4442 (Linux TCP_QUEUE_SEQ), CVE-2026-68322 (Linux RDS over IPv6) and CVE-2026-73549 (Envoy, scoped IPv6 addresses). None concerns glibc.
- https://github.com/bminor/glibc/commit/f545ad4928fa1f27a3075265182b38a4f939a5f7 — retrieved 2026-10-29 — "The sunrpc function svcunix_create suffers from a stack-based buffer overflow with overlong pathname arguments." The subject is "CVE-2022-23218: Buffer overflow in sunrpc svcunix_create (bug 28768)". The NEWS entry reads "Passing an overlong file name to the svcunix_create legacy function could result in a stack-based buffer overflow." The old code did a memcpy into addr.sun_path with no length check. The fix calls `__sockaddr_un_set` first and returns NULL on failure, and the new test expects errno EINVAL. This is a mirror of sourceware's glibc, read by hash.
- https://github.com/bminor/glibc/commit/9c443ac4559a47ed99859bd80d14dc4b6dd220a1 — retrieved 2026-10-29 — "increment the pointer to the header before checking the stride of the increment against available space." The subject is "socket: Check lengths before advancing pointer in CMSG_NXTHDR" (BZ #28846). The new order is: reject cmsg_len smaller than struct cmsghdr, compute the padding, check that the remainder holds the current and next header and that cmsg_len fits, and only then advance. The regression test tst-cmsghdr covers a first header filling the buffer, cmsg_len of SIZE_MAX, and exactly enough or one byte too little room for another header. This is a mirror read by hash, and the date is not shown.
- https://openwall.com/lists/musl/2025/12/29/1 — retrieved 2026-10-29 — "Most libc implementations allow this, glibc and most from the BSD-family from what I can tell." The post is "Re: [PATCH] fix CMSG_NXTHDR result when cmsghdr ends exactly before __MHDR_END", Gabriel Hansson, 2025-12-29. musl's boundary check returns NULL when a header ends exactly at the end of the control buffer, i.e. a zero-length final payload. The poster writes "The question is more about whether zero-sized payloads should be allowed or not." He says POSIX permits NULL only when the data extends beyond the end, and that compatibility tests in Rust's libc crate began failing. The post does not say whether the patch was applied.
- https://github.com/torvalds/linux/commit/6900317f5eff0a7070c5936e5383f589e0de7a09 — retrieved 2026-10-29 — "this can happen when an odd number of fds are being passed over AF_UNIX sockets." The commit is "net, scm: fix PaX detected msg_controllen overflow in scm_detach_fds" (Daniel Borkmann). CMSG_SPACE() adds 4 bytes of tail padding that CMSG_LEN() does not. A receive buffer without them makes msg->msg_controllen wrap "to a length of 18446744073709551612 bytes" in the commit's 20-byte, one-fd example. The fix clamps cmlen to msg_controllen (+2 lines in net/core/scm.c). There is no Fixes tag because the bug predates the 2002 start of the history tree. This is a mirror read by hash.
- https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2013-1979 — retrieved 2026-10-29 — "The scm_set_cred function in include/net/scm.h in the Linux kernel before 3.8.11 uses incorrect uid and gid values" (excerpt). Published 2013-05-03, status Modified, CWE-264. The references name kernel commit 83f1b4ba917db5dc5a061a44b3403ddb6e783494, ChangeLog-3.8.11, oss-security 2013/04/29/1 and Red Hat bugzilla 955629. None was opened.

## What would change this

The request's condition is that a defect class reaches one of the five places that the specifications' rules do not already refuse or test. If so, the rule and its test are amended before the cycle that owns them, and a defect that asks the language a question (a layout, a refusal) becomes a probe of this subcycle first.

**Verdict: not settled by this digest.** The condition has two halves.
- **First half, met.** Defect classes do reach the five places: D1 to D8 below, each read at a primary.
- **Second half, not judged.** This run read nothing on the machine, so it has not seen A-19, A-13, N-2, N-9 to N-11, N-13 to N-17 or the cycle tests. Whoever holds those rules settles it line by line.
- **What a mismatch means.** A D line with no matching rule text means this digest changes the plan for that rule and its test, and the libraries' seat rules first.
- **Where to look first.** On the evidence alone, the least famous classes, and so the likeliest to be missing, are D3, D6 and D7, and D5's SIZE_MAX case. That is my reading of the evidence, not a finding about the rules.

Rule IDs come from the request's own feeds line. It names no separate rule for `SCM_RIGHTS` decode, so D7's mapping is a reading.

- **D1 — leading zeros (A-19, SK-036; held there, not a probe).** Refuse any leading zero in a decimal field of address text at every parser entry point. A second parser in the same project re-opened it (Go `net`, then `net/netip`), and the class recurred as late as 2025 in Perl CIDR strings. The evidence does not show whether embedded IPv4 inside an IPv6 literal was hit in Python, Go or Rust.
- **D2 — abbreviation and group counting (A-19; test vectors).** The IPv6 `::` path must not write past its group storage (musl CVE-2015-1817). musl also fixed a lone `::` and its failure returns (2011, 2013). The tests need inputs with too many groups, several `::`, a lone `::` and the failure return.
- **D3 — initialisation on the IPv4-in-IPv6 path (A-19; asks the language, P3).** No result byte may be left unwritten on any success or failure path (musl 7e13e5ae, no CVE).
- **D4 — overlong `sockaddr_un` path (A-13; asks the language, P3).** An overlong path is refused before any copy into `sun_path` (EINVAL in glibc's regression test). Where the exact limit sits, 107 plus NUL or 108 without NUL, was not read.
- **D5 — walk arithmetic (N-2, N-9 to N-11; asks the language, P1 and P4).**
  - No pointer or offset moves before the length check.
  - A `cmsg_len` below the header size ends the walk.
  - A `cmsg_len` of SIZE_MAX cannot wrap.
  - glibc's tst-cmsghdr case families can seed the test vectors.
- **D6 — final empty header (N-9 to N-11; test vector, not a probe).** A header with an empty payload that ends exactly at the control buffer's end is returned by the walk. musl returns NULL; per the poster, glibc and most BSD libcs return it. The digest shows only that implementations disagree and that no outcome was stated.
- **D7 — tail padding (N-2, N-9 to N-11, `SCM_RIGHTS` receive side; asks the language, P1 and P2).** The last header's padded length can exceed what the control length holds (CMSG_SPACE versus CMSG_LEN, 4 bytes for an odd descriptor count). An aligned length is never subtracted from a smaller remainder. The kernel commit's 20-byte, one-fd example is a ready vector.
- **D8 — identity values (N-13 to N-17; held, not a probe).** Identity is whatever the kernel fills in, and the kernel has shipped wrong uid and gid values in credential passing (CVE-2013-1979, before 3.8.11). The library's tests can pin its own decode and nothing more. No record was read for `SO_PEERCRED` as such.

Probe candidates are questions to the language. The compiler tree, not the web, answers them.
- **P1.** Does `usize` addition or subtraction wrap, trap or check on overflow and underflow? (D5, D7)
- **P2.** What are the size, alignment and tail padding of a header-shaped struct and of its padded data area? (D7)
- **P3.** For a struct holding a 108-byte path array: what is its size, does an out-of-range write trap, and do unassigned elements read as zero? (D2, D3, D4)
- **P4.** Is a header view over a byte slice shorter than the header bounds-checked? (D5; Go's over-read #17649 is a lead.)

Every other D line is held where its subject is decided.

## Confidence and gaps

**Confidence: medium on what is stated, low on completeness.** Each item was read at the primary named, on 2026-10-29. The 12-fetch budget is spent. Two fetches returned nothing usable, and the registry sweeps cover two keywords. A keyword search matches description text only, so a sweep is a floor, not a census. The reference set read was glibc, musl, CPython, Go, Rust std and the Linux kernel.

**Two independent primaries (registry plus project record):**
- Python CVE-2021-29921: NVD plus CPython PR 25099.
- Go CVE-2021-29923: NVD plus golang/go#49365's account of the 1.17 change.
- musl CVE-2015-1817: NVD plus the musl log. The link from the CVE to commit fc13acc3 is made only by the advisory, which was not opened.

**One primary only (1P):**
- Rust CVE-2021-29922: NVD only; fix PR rust-lang/rust#83652 and issue #83648 are in its references, not opened.
- The `net/netip` regression: #49365 only; commit 3796df1 not opened.
- musl 7e13e5ae and the 2011/2013 fixes: log only.
- glibc CVE-2022-23218: commit only; no registry record opened.
- glibc BZ 28846: the commit by mirror only.
- The musl December 2025 post: a patch proposal with no outcome.
- Kernel 6900317: commit only.
- CVE-2013-1979: NVD only; its commit was not opened.

cve.org was not fetched. NVD republishes the CVE List, so a cve.org copy would not be an independent second primary.

**Unusable fetches, both counted in the 12:**
- The NVD web search page returned only its title. The page is script-driven, so the NVD API was used instead.
- sourceware.org Bugzilla returned an Anubis access-denied page (error code 9e4edb5b6b850c41). glibc's tracker records (BZ 28846, 13500, 28768, 22542) and sourceware git were therefore unread.
- glibc facts come from the bminor/glibc GitHub mirror and kernel facts from torvalds/linux on GitHub, both by commit hash, not from the canonical hosts.

**Unresolved at the budget, in the order I would spend a follow-up.** The leads come from 27 web searches that only located pages. None is cited above, and each needs a fetch before anything rests on it.
1. NVD keyword sweeps not run: `CMSG_NXTHDR`, `SCM_RIGHTS`, `SCM_CREDENTIALS`, `SO_PEERCRED`, `sockaddr_un`, `inet_aton`. Lead for `SCM_RIGHTS`: CVE-2021-0920 (unix GC race, use-after-free; lifetime, not decode).
2. A-13:
   - glibc `socket/sockaddr_un_set.c` at a tag, where glibc's rule for an exactly-108-byte name lives (unread).
   - glibc CVE-2022-23219 (clnt_create, bug 22542).
   - CPython bpo-8372: `makesockaddr` assumes a NUL-terminated `sun_path`, while Linux allows all 108 bytes unterminated.
   - Go `syscall.SockaddrUnix` and Rust `UnixListener::bind` length rules.
3. N-13 to N-17:
   - Kernel commit 83f1b4ba and CVE-2013-1958 (`scm_check_creds`, pid namespaces, kernels before 3.8.6).
   - A stable-queue account that CVE-2013-1979 came from commit 257b5358b32f switching to effective uid and gid.
   - LKML threads on `SO_PEERCRED` versus `SCM_CREDENTIALS` and pid translation.
   - The kernel change setting MSG_CTRUNC for all SCM types, i.e. silent truncation of credentials.
   - pid reuse and pidfd options (`SO_PEERPIDFD`, `SCM_PIDFD`), named from recollection and not searched.
4. N-2, N-9 to N-11:
   - glibc BZ 13500: reading `cmsg_len` of an uninitialised next header while building ancillary data, with Austin Group bug 1056 and glibc's follow-up "convert_scm_timestamps: Initialize buffer for CMSG_NXTHDR".
   - musl commit 81fb75a1d75c… (undefined behaviour in `CMSG_NXTHDR`).
   - Go #41522 (`ParseSocketControlMessage` panic), #17649 (header copy over-read) and #56384 (EINVAL for a nil-payload message, possibly the D6 class).
   - Rust std's `SocketAncillary` is nightly-only.
5. A-19:
   - Rust PR #83652.
   - Go CVE-2024-24790 (netip `Is*` methods on IPv4-mapped IPv6), CVE-2024-45341 (`net.ParseIP` rejects IPv6 zones while `netip.ParseAddr` accepts them) and #63850 (`netip.ParsePrefix` accepts "/+24" and leading zeros in the length; status unconfirmed).
   - Python CVE-2024-4032 (`is_private`/`is_global`), CVE-2024-11168 (urllib bracketed hosts; the patch touches ipaddress scope-id code) and CPython #129538 (IPv6Interface loses a scope id).
   - The musl advisory naming the commit that introduced CVE-2015-1817.
   - glibc's and musl's own `inet_pton` and `inet_aton` behaviour (leading zeros, octal) was never read at their primaries. Python's PR and Go's issue state it only from the outside.
6. Not searched at all: FreeBSD, OpenBSD and NetBSD kernels and libcs.

Budget use: 12 of 12 fetches (10 usable, 2 empty). The digest is stale on 2027-01-27 and is re-run at the hardening cycle.
