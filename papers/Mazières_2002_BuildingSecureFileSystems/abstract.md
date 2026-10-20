# Abstract

## Original Text (Verbatim)

This paper shows how to implement a trusted network file system on an untrusted server. While cryptographic storage techniques exist that allow users to keep data secret from untrusted servers, this work concentrates on the detection of tampering attacks and stale data. Ideally, users of an untrusted storage server would immediately and unconditionally notice any misbehavior on the part of the server. This ideal is unfortunately not achievable. However, we define a notion of data integrity called *fork consistency* in which, if the server delays just one user from seeing even a single change by another, the two users will never again see one another's changes—a failure easily detectable with on-line communication. We give a practical protocol for a multi-user network file system called SUNDR, and prove that SUNDR offers fork consistency whether or not the server obeys the protocol.

---

## Our Interpretation

The problem is freshness and integrity of shared data on a server that may lie by withholding updates, which signatures alone cannot detect. The key result is fork consistency, achieved by having every user sign a version vector of everyone's versions, so any concealment splits users into groups that can never re-merge undetected. It gives propstore a precise target guarantee for multi-author federation over untrusted hosts.
