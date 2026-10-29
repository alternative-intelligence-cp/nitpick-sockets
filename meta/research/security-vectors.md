# Current test vectors for IPv4/IPv6 text addresses, cmsghdr and SCM_RIGHTS — research digest

**As of 2026-10-29.** Question: which published test-vector sets exist for IPv4 and IPv6 text-address parsing and formatting, and for `cmsghdr` and `SCM_RIGHTS` handling, at what current versions or revisions, and where is each one's primary copy?

## Answer
Nothing found is a maintained vector set for the plan's whole semantics (RFC 5952 output, strict input refusal, cmsghdr walking, SCM_RIGHTS). Only partial sets exist, and none is a standalone data file for inet_pton/inet_ntop or for cmsg handling. 16 searches, one of them extended, found no such file, and absence cannot be proven. The sets verified, each with its primary copy and the revision to pin as of 2026-10-29, are these.
- **(1) RFC 5952.** August 2010, Proposed Standard, updates RFC 4291; primary copy rfc-editor.org/rfc/rfc5952, read at the IETF datatracker; no obsoleting or updating RFC shown. Its examples are prose, and they govern output only, because parsers must accept any RFC 4291 form. Its 12 errata (1 verified editorial, 4 held, 7 rejected) change no address example.
- **(2) os-test.** Primary gitlab.com/sortix/os-test, ISC licence. Pin HEAD 8e790a45188ac67b550ba62cdde4103b253f5ce8 of 2026-10-19, because its newest "published-*" tag is dated 2025-07-25. `basic/arpa_inet/inet_ntop.c` holds 9 vectors (2 IPv4, 7 IPv6) that enforce RFC 5952: no leading zeros, lowercase, leftmost-longest "::", no "::" for a single zero field, "::", and "::ffff:1.2.3.4".
- **(3) glibc `resolv/tst-inet_pton.c`.** Primary sourceware.org/git/glibc.git, LGPL-2.1-or-later; read on master on 2026-10-29, release tag not resolved. It is a 106-entry accept/refuse table with expected bytes, of which 4 entries are accepted as AF_INET and 37 as AF_INET6. Among its refusals are a leading-zero octet ("192.0.2.01"), a trailing dot, octets over 255, five-digit IPv6 groups and a doubled "::".
- **(4) web-platform-tests `url/resources/urltestdata.json`.** Primary github.com/web-platform-tests/wpt; last changed by c48d58747e1f211527fb695fd60548a997fae617 on 2026-09-19. It is the only JSON data file found. Its path and latest commit title mark it as a URL-parser file, and I did not open its contents.
- **(5) cmsghdr and SCM_RIGHTS.** Only test programs exist. The one verified is the Linux selftests in `tools/testing/selftests/net/af_unix`, primary git.kernel.org torvalds/linux.git. Its latest commit is 02e658dffe501640079ad78c8fdd7eb6e1a5e4dc of 2026-10-12. `scm_rights.c` was extended by b645ccd410547d0e0e4a9543f828119e24dc7635 on 2026-09-15. LSM-denial SCM_RIGHTS tests were added by 5d513ce19de963c7e36904c98d7b02ecd16a30a1 on 2026-08-18.

glibc's cmsg tests, FreeBSD, CPython and musl were located by search only (last section).

## Evidence
- https://datatracker.ietf.org/doc/html/rfc5952 — retrieved 2026-10-29 — header "Updates: 4291", "Category: Standards Track", "August 2010", "RFC - Proposed Standard"; the page shows no Obsoletes, Obsoleted by or Updated by line. Examples: "2001:0db8::0001 is not acceptable and must be represented as 2001:db8::1." / "2001:db8:0:0:0:0:2:1 must be shortened to 2001:db8::2:1." / "the representation 2001:db8:0:1:1:1:1:1 is correct, but 2001:db8::1:1:1:1:1 is not correct." / "For example, 2001:db8::1:0:0:1 is correct representation." / "(i.e., ::ffff:192.0.2.1 instead of 0:0:0:0:0:ffff:192.0.2.1)". Parse side: "all implementations MUST accept and be able to handle any legitimate [RFC4291] format." The 3-zero-field example in 4.2.3 prints as "2001: 0:0:1:0:0:0:1" with no stated result; the result 2001:0:0:1::1 is derived from the rule, not quoted.
- https://errata.rfc-editor.org/rfc/rfc5952 (the www.rfc-editor.org/errata URL redirects here) — retrieved 2026-10-29 — the extraction lists 12 errata: Verified 2498; Held for Document Update 6272, 8554, 3218, 3219; Rejected 2656, 2872, 3884, 4483, 4985, 4900, 4986. Erratum 8554 (held 2025-09-04): "Arose while drafting RFC 9844. A future revision might reference RFC 9844." Erratum 2656 (rejected, uppercase hex): "This errata is attempting to overturn the clear consensus of the WG." Erratum 2872 (rejected): "::1 and :: are more specific and not part of the reserved block for IPv4 compatible addresses."
- https://sortix.org/os-test/ — retrieved 2026-10-29 — "os-test is licensed under the ISC license, see the LICENSE file in the source code for details." / "basic: This suite tests basic invocations of all functions." / "include: This suite tests whether headers include the correct declarations." Repository link: https://gitlab.com/sortix/os-test.
- https://gitlab.com/sortix/os-test/-/raw/HEAD/basic/arpa_inet/inet_ntop.c — retrieved 2026-10-29 — header "/* Test whether a basic inet_ntop invocation works. */"; "// Enforce RFC 5952 for IPv6 addresses, even though it is techically not" (the extraction stops mid-comment); "// Test the leftmost :: is preferred if two sequences have the same length."; "// Test :: is not used to shorten a single field.". Expected strings: "1.2.3.4", "255.255.255.255", "123:4567:89ab:cdef:cafe:babe:dead:beef", "123::cdef:cafe:0:0:beef", "::89ab:cdef:cafe:0:0:beef", "123:0:0:cdef::beef", "123:4567:89ab:cdef:0:babe:dead:beef", "::", "::ffff:1.2.3.4". The file carries no licence line of its own.
- https://gitlab.com/api/v4/projects/sortix%2Fos-test/repository/commits?per_page=3 — retrieved 2026-10-29 — "id":"8e790a45188ac67b550ba62cdde4103b253f5ce8","committed_date":"2026-10-19T15:02:57.000+02:00","title":"Fix regression in attempted fix of regex bracket-range-collate."
- https://gitlab.com/api/v4/projects/sortix%2Fos-test/repository/tags?per_page=5 — retrieved 2026-10-29 — first tag returned: "name":"published-2025-07-25","commit_id":"2515b84b92f5439d92056dacb717efbb2fd373cf","committed_date":"2025-07-25T23:31:36.000+02:00".
- https://raw.githubusercontent.com/bminor/glibc/master/resolv/tst-inet_pton.c — retrieved 2026-10-29 (GitHub mirror of sourceware's glibc.git) — "Copyright (C) 2017-2026 Free Software Foundation, Inc."; "The test cases were manually crafted and the set enhanced with American Fuzzy Lop."; struct fields "True if AF_INET parses successfully." and "True if AF_INET6 parses successfully."; every case is also run through `__inet_pton_length` on a non-NUL-terminated buffer. Rows, as the extraction listed them (106 entries): AF_INET accepted: 0.0.0.0, 127.0.0.1, 192.0.2.27, 255.255.255.255; refused for both families: 192.0.2.01, 192.0.2.1., 192.0.2.256, 10.0.301.2, 2001:db8:00001::f, 5::5::; accepted as AF_INET6: 2001:db8::00, ::ffff:127.0.0.1, F::.
- https://api.github.com/repos/web-platform-tests/wpt/commits?path=url/resources/urltestdata.json&per_page=1 — retrieved 2026-10-29 — "sha": c48d58747e1f211527fb695fd60548a997fae617, committer date 2026-09-19T11:24:24Z, "Test constructor as a non-special URL scheme".
- https://api.github.com/repos/torvalds/linux/commits?path=tools/testing/selftests/net/af_unix&per_page=12 — retrieved 2026-10-29 (GitHub mirror of kernel.org; same commit ids) — 02e658dffe501640079ad78c8fdd7eb6e1a5e4dc 2026-10-12T08:58:21Z "selftests/net: SO_PEERPIDFD_THREAD"; b645ccd410547d0e0e4a9543f828119e24dc7635 2026-09-15T23:45:05Z "selftest: af_unix: Add test case with mixed lowpoint in scm_rights.c."; 5d513ce19de963c7e36904c98d7b02ecd16a30a1 2026-08-18T01:14:52Z "selftest: Add tests for useful handling of LSM denials on SCM_RIGHTS".

## What would change this
The request's two conditions, judged on the evidence above:

1. **A maintained vector set that cycle 0.1's conformance stage should pin instead of hand-written cases: not met.**
   - No verified set covers RFC 5952's canonical forms and a refusal table together, and none is a data file. os-test (9 formatting vectors) and glibc (106 parse vectors) are C tables. Using either means transcribing rows and recording the pinned revision as provenance. Their licences differ (ISC; LGPL-2.1-or-later), which matters if rows are copied.
   - The RFC's own examples and A-19's table, which was not available to me, stay as hand-written cases.
   - A weak form is met. Both tables are maintained (os-test HEAD 2026-10-19; glibc master with a 2026 copyright line) and usable as cross-check corpora, each worth a CURRENCY.md row if the seat wants one. Compare glibc's rows against A-19 row by row.
   - WPT's JSON could change this only after its rows are opened. Its path and latest commit title mark it as a URL-parser file, which probably follows URL rules rather than inet_pton or RFC 5952 rules. That is not verified here.
   - For cycle 0.5 no maintained cmsg/SCM_RIGHTS vector set exists. The kernel selftests are kernel-run programs still being extended (2026-08-18, 2026-09-15), so a 0.5 pin names a SHA or a kernel release.
2. **A cited set with a newer revision: not met for RFC 5952.**
   - The datatracker shows no obsoleting or updating RFC.
   - The RFC Editor errata page holds four errata for a future document update, none published.
   - A search found no 5952bis draft.
   - One lead could meet this condition for any specification that cites RFC 6874 (IPv6 zone identifiers in URIs). Search summaries of the RFC Editor and datatracker pages for RFC 9844 (August 2025, "Entering IPv6 Zone Identifiers in User Interfaces") report that it obsoletes RFC 6874. I could not open it within the budget. The seat should check whether any specification cites RFC 6874 before step 0.

On this reading the digest does not require a plan change; the libraries' seat rules.

## Confidence and gaps
**Confidence: medium.** It is high for what was opened: the RFC 5952 text and errata, the os-test file and revision, the glibc table, and the WPT and kernel SHAs as the GitHub API reported them. It is lower for the rest:
- The negative claim (no standalone vector set) rests on 16 searches (one extended) and cannot be proven.
- Quotations are as relayed by the fetch tool's extraction, not raw bytes. Re-read each file at its pinned revision before transcribing any vector.
- The glibc and kernel facts were read through GitHub mirrors (bminor/glibc, torvalds/linux), not sourceware.org or kernel.org. Commit ids are identical across mirrors.
- glibc is pinned to "master on 2026-10-29" because the `glibc-2.44` tag path returned HTTP 404 on the mirror. The kernel release number was not resolved.
- Two independent primaries were reached only for RFC 5952's canonical rules: the RFC text and os-test's separately written test agree.
- Single primary only: RFC 5952's "no newer revision" (datatracker alone; https://www.rfc-editor.org/info/rfc5952 returned HTTP 502 and was not retried; the errata page shows no relationship fields), glibc's table, the kernel selftests, and the WPT revision. WPT's contents were not opened.
- Budget: 12 of 12 fetches used. One returned 502, one 404, and one was a cross-host redirect that cost a call to follow.

**Unresolved at the budget** (all are leads, not cited):
- WPT rows, and the WHATWG URL Standard's host parser and serializer.
- glibc `socket/tst-cmsghdr.c` with its skeleton (2022, CMSG_NXTHDR bounds; https://patchwork.sourceware.org/project/glibc/patch/20220720090241.3235289-1-arjun@redhat.com/) and `sysdeps/unix/sysv/linux/tst-scm_rights.c`.
- FreeBSD `tests/sys/kern/unix_passfd_test.c` (https://reviews.freebsd.org/D35315, https://reviews.freebsd.org/D57426).
- CPython `Lib/test/test_socket.py` (CMSG_LEN/CMSG_SPACE, SCM_RIGHTS, truncation; https://remotebranch.eu/Stowage/cpython/commit/7291108d88ea31d205da4db19d202d6cbffc6d93).
- musl libc-test `src/functional/inet_pton.c` (https://openwall.com/lists/musl/2013/10/21/7).
- os-test `basic/arpa_inet/inet_pton.c`, and any CMSG_* or SCM_RIGHTS coverage under its `include/` and `basic/sys_socket`.
- RFC 4291's status (its -bis draft showed as expired in a search summary; https://datatracker.ietf.org/doc/draft-ietf-6man-rfc4291bis/).
- RFC 9844 (https://www.rfc-editor.org/info/rfc9844).
- POSIX Issue 8 inet_ntop/inet_pton and `<sys/socket.h>`, and RFC 3542 section 20.
- The plan's own specifications and A-19, not read by instruction.

Not surveyed: the Rust core::net, Go net/netip and CPython ipaddress unit tests. gVisor's syscall tests were searched for twice and not located.

**Stale after 2027-01-27** (security: 90 days from 2026-10-29).
