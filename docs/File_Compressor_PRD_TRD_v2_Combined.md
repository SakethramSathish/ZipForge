# Build Your Own File Compressor — PRD + TRD

## Product Requirements Document

# Product Requirements Document (PRD)

## Project: Build Your Own File Compressor
**Document Version:** 2.0  
**Status:** Implementation Ready  
**Product Type:** Streamlit-based file compression, archive, decompression, and image optimization application  
**Primary Language:** Python 3.12+  
**Primary Frontend:** Streamlit  
**Archive Extension:** `.fcmp`  
**Core Compression:** Custom implementations of RLE, Huffman Coding, and LZW  
**Image Processing:** Pillow-based optimization  
**Last Updated:** September 2026

---

# 1. Executive Summary

**Build Your Own File Compressor** is a technically rigorous compression utility designed to demonstrate how file compressors and archive applications work internally while remaining practical for everyday use.

The product has two related but intentionally distinct workflows:

1. **Lossless general-file compression** using custom implementations of:
   - Run-Length Encoding (RLE)
   - Huffman Coding
   - LZW
   - `STORE` fallback when compression would increase size

2. **Image compression and optimization** using controlled image encoding and quality/size optimization, including a dedicated **Target Size** mode.

The system will provide a polished **Streamlit frontend** through which users can upload one or multiple files, compress/decompress archives, inspect metadata and compression statistics, optimize images, and download results.

A major differentiating feature is **Compress to Target Size** for images. The user can specify a maximum size in KB or MB, and the application will search for the highest practical image quality that produces an output at or below that target whenever technically achievable.

The project is intended to be both:

- a usable compression utility; and
- a demonstration of data structures, algorithms, binary file handling, serialization, integrity verification, performance engineering, and software architecture.

---

# 2. Product Vision

Create a transparent, reliable, extensible compression platform that exposes the engineering concepts behind compression rather than hiding them behind existing archive libraries.

### Vision Principles

1. **Correctness before compression ratio.**
2. **Core compression algorithms must be implemented by the project.**
3. **Lossless and image-quality-based workflows must be clearly distinguished.**
4. **Archives must use a documented, versioned custom format.**
5. **Every displayed size, ratio, or benchmark must come from real execution.**
6. **The interface should be simple for non-technical users while still exposing useful technical information.**
7. **The architecture must support future algorithms and streaming without requiring a complete rewrite.**
8. **Untrusted archives must be parsed defensively and extracted safely.**

---

# 3. Problem Statement

Most archive applications make compression appear to be a single operation while hiding:

- frequency analysis,
- dictionary construction,
- entropy coding,
- bit-level packing,
- metadata serialization,
- archive layout,
- checksums,
- error detection,
- and the trade-off between quality and file size.

This project provides a complete and inspectable pipeline:

```text
Input
  ↓
File Discovery
  ↓
Analysis / Mode Selection
  ↓
Compression or Image Optimization
  ↓
Binary Encoding
  ↓
Custom Archive / Image Output
  ↓
Integrity Validation
  ↓
Download / Extraction
```

The product should make this pipeline understandable without making the user operate a low-level command-line tool.

---

# 4. Goals and Objectives

## 4.1 Primary Goals

- Compress one or multiple general files losslessly.
- Decompress generated `.fcmp` archives accurately.
- Implement RLE, Huffman, and LZW internally.
- Compare original and compressed sizes.
- Calculate compression ratio and percentage reduction.
- Preserve required file metadata.
- Detect corruption and invalid archives.
- Support safe extraction.
- Provide a polished Streamlit user interface.
- Support image compression with three user-friendly compression levels.
- Support target-size image optimization.
- Benchmark algorithm performance using real files.

## 4.2 Secondary Goals

- Make algorithm selection understandable.
- Allow archive inspection.
- Provide useful error messages.
- Keep core modules independently testable.
- Maintain a clear developer-oriented architecture.
- Provide documentation suitable for an academic project, portfolio, and technical demonstration.

---

# 5. Non-Goals for the MVP

The following are explicitly outside the MVP unless later approved:

- Cloud storage integration.
- User accounts and authentication.
- Distributed compression.
- Server-side multi-user job scheduling.
- End-to-end encryption.
- Password-protected archives.
- GPU-specific compression.
- Native C++ acceleration.
- Arbitrary target-size guarantees for general lossless files.
- Reimplementation of JPEG/WebP codecs from scratch.

These may appear in future scope.

---

# 6. Target Users

### 6.1 Students and Developers

People who want to understand:

- compression algorithms,
- binary formats,
- bit manipulation,
- archives,
- and performance optimization.

### 6.2 General Users

Users who want to:

- shrink files,
- package multiple files,
- inspect archives,
- or reduce image sizes.

### 6.3 Technical Reviewers / Interviewers

People evaluating:

- algorithmic knowledge,
- architecture,
- implementation quality,
- testing,
- and systems understanding.

---

# 7. Core Product Features

## 7.1 General File Compression

Users can upload one or multiple files.

The system should:

1. Read file metadata.
2. Determine a compression strategy.
3. Compress the data.
4. Compare the output against the original.
5. Use `STORE` when the compressed payload is not beneficial.
6. Record algorithm metadata.
7. Store integrity information.
8. Package the result in the `.fcmp` format.

---

# 8. Compression Algorithms

The MVP shall include:

### RLE — Run-Length Encoding

Useful for data containing long repeated sequences.

### Huffman Coding

Frequency-based entropy coding using variable-length codes.

### LZW — Lempel-Ziv-Welch

Dictionary-based compression suitable for repeated patterns.

### STORE

A no-compression representation used when compression provides no benefit.

The system must not present these algorithms as universally optimal. Compression effectiveness depends on the input data.

---

# 9. Automatic Algorithm Selection

Provide an **Automatic** mode for general files.

The system may:

- inspect the input;
- attempt candidate algorithms;
- measure compressed size;
- consider processing cost;
- select the most appropriate representation.

For the MVP, selection must be deterministic and documented.

The product should never fabricate a compression ratio or assume an algorithm is better without measuring or using a justified rule.

---

# 10. Multi-File and Folder Support

The application should support:

- multiple uploaded files;
- folder selection where supported by the execution environment;
- relative directory structure preservation;
- per-file compression metadata;
- per-file integrity verification.

The archive must restore the intended file structure during extraction.

---

# 11. Custom `.fcmp` Archive

The product will use a custom archive format with:

- magic/signature;
- format version;
- global flags;
- file count;
- per-entry metadata;
- algorithm identifier;
- original size;
- compressed size;
- integrity hash;
- algorithm-specific metadata;
- compressed payload.

The archive format must be documented and versioned.

The format should be designed so additional algorithms can be added later.

---

# 12. Archive Inspection

Users should be able to inspect an `.fcmp` archive without extracting it.

The application should display, where available:

- archive version;
- number of entries;
- filenames;
- original sizes;
- compressed sizes;
- selected algorithm;
- compression ratio;
- integrity status;
- metadata.

---

# 13. Decompression and Extraction

Users can upload a `.fcmp` archive and extract it to a chosen location or download extracted files.

The application must:

- validate archive structure;
- validate metadata;
- reject unsupported versions;
- reject unsupported algorithms;
- verify payload boundaries;
- decompress;
- verify integrity;
- safely handle output paths.

The application must not silently report success if integrity verification fails.

---

# 14. Image Compression

Images are a separate product workflow because many modern image formats use quality/encoding parameters and may be compressed lossily.

Supported input/output formats should include practical common formats such as:

- JPEG
- PNG
- WebP

Additional formats may be added when well-supported by the selected Python libraries.

Image processing must correctly account for:

- RGB;
- RGBA;
- grayscale;
- transparency;
- orientation metadata;
- common EXIF metadata.

---

# 15. Image Compression Levels

The UI must include three predefined modes inspired by the supplied reference design.

## EXTREME COMPRESSION

User-facing description:

> Lower quality, maximum compression

Purpose:

- minimize file size;
- accept more visible quality loss.

## RECOMMENDED COMPRESSION

User-facing description:

> Good quality, good compression

Purpose:

- balanced visual quality and size.

This must be the default.

## LESS COMPRESSION

User-facing description:

> Higher quality, lower compression

Purpose:

- prioritize visual fidelity over size reduction.

The exact encoder parameters must be benchmarked and configurable internally.

---

# 16. Target Size Image Compression

The application must provide a dedicated mode:

> **Compress to Target Size**

The user can enter a desired maximum:

```text
Target Size: 500 KB
```

or:

```text
Target Size: 2 MB
```

The system should attempt to generate:

```text
final_size <= target_size
```

while maximizing achievable image quality.

The target-size feature is a constrained optimization problem, not a fixed quality preset.

---

# 17. Target Size Optimization Behavior

The optimizer should:

1. Load/analyze the image.
2. Establish supported output representation(s).
3. Set a quality search interval.
4. Encode a candidate.
5. Measure the result.
6. Determine whether the result is above or below the target.
7. Adjust quality using binary search or another efficient bounded search.
8. Keep the highest-quality candidate satisfying the target.
9. Stop after a bounded number of iterations.
10. Return the best valid result.

Conceptually:

```text
                    Image
                      ↓
                 Encode Candidate
                      ↓
                Measure Size
                      ↓
               Is size <= target?
                 /           \
               No             Yes
               ↓               ↓
          Lower quality    Save candidate
                               ↓
                         Try higher quality
                               ↓
                         Continue search
                               ↓
                   Highest valid quality
```

---

# 18. Target Size Definition of "Best Quality"

For the MVP, "best quality" means:

> **the highest encoder quality parameter found within the search bounds that produces an output at or below the requested target size.**

Do not claim that this is a mathematically perfect perceptual optimum.

A future version may incorporate perceptual metrics such as SSIM or other quality measures.

---

# 19. Target Size Edge Cases

### Target larger than original

Do not unnecessarily degrade the image.

### Target close to original size

Preserve as much quality as possible.

### Extremely small target

Attempt optimization, but respect a configured minimum quality/viability threshold.

If the target cannot be reached within acceptable quality limits:

```text
Target could not be reached without exceeding
the configured minimum quality threshold.
```

The system must report this honestly.

---

# 20. Image Comparison UI

After compression, display original and compressed images side by side where practical.

Show:

```text
Original Size
Compressed Size
Bytes Saved
Reduction %
Output Format
Quality
Target Size
Target Achieved
Optimization Iterations
Processing Time
```

---

# 21. Compression Results

For general files:

```text
Original Size
Compressed Size
Bytes Saved
Compression Ratio
Reduction %
Algorithm
Processing Time
Integrity Status
```

For image compression:

```text
Original Size
Final Size
Bytes Saved
Reduction %
Output Format
Quality
Compression Level
Target Size
Target Status
Processing Time
```

All metrics must come from actual processing.

---

# 22. Batch Processing

The application should support batch operations.

For multiple files, display a result table containing:

```text
Filename
Original Size
Compressed Size
Reduction
Algorithm / Format
Status
```

Batch failures should be isolated so one bad file does not automatically invalidate unrelated successful operations.

---

# 23. User Experience Requirements

The UI should be:

- clean;
- modern;
- responsive;
- understandable;
- visually consistent;
- suitable for both demonstrations and real usage.

Avoid overwhelming the main screen with technical implementation details.

Advanced algorithm information should be accessible through expandable sections or dedicated pages/tabs.

---

# 24. Suggested Streamlit Navigation

A recommended layout is:

```text
FILE COMPRESSOR

[ General Compression ]
[ Image Compression ]
[ Target Size ]
[ Decompress ]
[ Archive Inspector ]
[ Benchmarks ]
```

A single-page UI with tabs is also acceptable if it results in a cleaner experience.

---

# 25. Progress Feedback

Long operations should provide progress feedback.

Examples:

```text
Compressing file...
██████████████████░░ 90%
```

For target-size optimization:

```text
Optimizing...
Target: 1.00 MB
Current Candidate: 1.12 MB
Quality: 78
Iteration: 5 / 8
```

The UI should never appear frozen during long operations when progress can reasonably be reported.

---

# 26. Integrity

The system must compute an integrity hash for files stored in `.fcmp` archives.

SHA-256 is recommended.

Flow:

```text
Original File
     ↓
SHA-256
     ↓
Compress
     ↓
Store Hash
     ↓
Decompress
     ↓
SHA-256 Again
     ↓
Compare
```

A mismatch must result in a clear integrity failure.

---

# 27. Security Requirements

Archives are untrusted input.

The system must defend against:

- path traversal;
- absolute extraction paths;
- malformed headers;
- invalid lengths;
- unsupported algorithms;
- corrupted payloads;
- oversized metadata claims;
- unexpected end-of-file conditions.

Example unsafe path:

```text
../../sensitive_file.txt
```

must never be allowed to escape the chosen extraction directory.

---

# 28. Performance Requirements

Measure:

- compression time;
- decompression time;
- throughput;
- original size;
- compressed size;
- compression ratio;
- image optimization iterations;
- image optimization time;
- peak memory where practical.

Benchmarks should include:

- text;
- source code;
- JSON;
- CSV;
- logs;
- repetitive data;
- random binary data;
- already compressed data;
- photographs;
- PNG graphics;
- small images;
- large images.

---

# 29. Reliability Requirements

The system must preserve byte-level equality for lossless workflows:

```text
decompress(compress(data)) == data
```

for all supported valid inputs.

No silent data loss is acceptable.

---

# 30. Persistence

The MVP does not require an external database.

Lightweight metadata/history may be stored in JSON where persistence is useful.

The compressor itself must remain functional without a persistent database.

---

# 31. Technology Requirements

### Required

- Python 3.12+
- Streamlit
- Pillow
- Python standard library
- pytest for tests

### Optional / Development

- Hypothesis for property-based tests
- psutil for memory measurements
- mypy for static type checking

Do not introduce unnecessary dependencies.

---

# 32. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Upload one or more files | Must |
| FR-02 | Compress general files | Must |
| FR-03 | Decompress `.fcmp` archives | Must |
| FR-04 | Implement RLE | Must |
| FR-05 | Implement Huffman coding | Must |
| FR-06 | Implement LZW | Must |
| FR-07 | Support STORE fallback | Must |
| FR-08 | Support custom `.fcmp` format | Must |
| FR-09 | Preserve required metadata | Must |
| FR-10 | Verify file integrity | Must |
| FR-11 | Secure extraction | Must |
| FR-12 | Show compression statistics | Must |
| FR-13 | Streamlit frontend | Must |
| FR-14 | Image compression | Must |
| FR-15 | Three image compression profiles | Must |
| FR-16 | Target-size image mode | Must |
| FR-17 | Target size in KB/MB | Must |
| FR-18 | Iterative quality optimization | Must |
| FR-19 | Before/after image preview | Should |
| FR-20 | Batch image processing | Should |
| FR-21 | Archive inspection | Should |
| FR-22 | Benchmark dashboard | Should |
| FR-23 | JSON history | Could |
| FR-24 | Streaming compression | Future |
| FR-25 | Encryption | Future |
| FR-26 | Cloud integration | Future |

---

# 33. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Correctness | Lossless workflows must round-trip exactly |
| Usability | Core actions should be understandable without technical knowledge |
| Reliability | Failures must be explicit and recoverable |
| Security | Unsafe archive extraction must be prevented |
| Performance | Avoid unnecessary copies and redundant encodings |
| Maintainability | Separate UI, services, algorithms, and infrastructure |
| Testability | Core algorithms must be testable without Streamlit |
| Extensibility | New algorithms should be registerable without rewriting the application |
| Portability | Avoid platform-specific path assumptions |
| Observability | Useful logs and diagnostic metrics |
| Documentation | Architecture, algorithms, format, usage, and limitations documented |

---

# 34. Acceptance Criteria

The MVP is considered complete when:

```text
[ ] General files can be compressed.
[ ] General files can be decompressed exactly.
[ ] RLE works independently.
[ ] Huffman works independently.
[ ] LZW works independently.
[ ] STORE fallback works.
[ ] Multiple files can be archived.
[ ] .fcmp metadata can be parsed.
[ ] Integrity verification works.
[ ] Corruption is detected.
[ ] Unsafe extraction is blocked.
[ ] Streamlit application is functional.
[ ] Images can be compressed.
[ ] Three image compression profiles work.
[ ] Recommended mode is the default.
[ ] Target-size mode accepts KB/MB.
[ ] Target-size optimization searches quality efficiently.
[ ] The final image is <= target whenever technically achievable.
[ ] Highest valid quality candidate is selected.
[ ] Impossible/poor targets are reported honestly.
[ ] Results display real measurements.
[ ] Tests pass.
[ ] Documentation is complete.
```

---

# 35. Future Scope

Potential future extensions:

- Streaming compression for large files.
- Encryption before archival.
- Password-protected archives.
- Parallel compression.
- C++ acceleration.
- Cloud storage integration.
- Compression presets for specialized file categories.
- More compression algorithms.
- Perceptual image quality metrics.
- Adaptive format selection.
- Resume/interrupted compression.
- Desktop packaging.

---

# 36. Success Metrics

The project should be evaluated on:

### Correctness

100% exact round-trip for supported lossless inputs.

### Reliability

Malformed/corrupted archives are detected safely.

### Usability

A first-time user can understand and complete a compression task without reading developer documentation.

### Performance

Benchmarks should establish actual speed and memory characteristics rather than relying on arbitrary targets.

### Technical Depth

The repository clearly demonstrates:

- algorithms;
- binary handling;
- archive design;
- optimization;
- testing;
- security;
- frontend integration.

---

# 37. Product Summary

The finished application should combine:

```text
Classic Compression Algorithms
          +
Custom Binary Archive Format
          +
Integrity Verification
          +
Modern Streamlit UI
          +
Image Compression Profiles
          +
Target-Size Optimization
          +
Benchmarking
          +
Security
```

The result should be both a useful utility and a substantial demonstration of systems and algorithmic engineering.


---

## Technical Requirements Document

# Technical Requirements Document (TRD)

## Project: Build Your Own File Compressor
**Document Version:** 2.0  
**Status:** Implementation Ready  
**Primary Language:** Python 3.12+  
**Frontend:** Streamlit  
**Archive Extension:** `.fcmp`  
**Core Algorithms:** RLE, Huffman Coding, LZW  
**Image Engine:** Pillow  
**Testing:** pytest (+ Hypothesis recommended)  
**Last Updated:** September 2026

---

# 1. Technical Overview

The application is a modular compression platform with two principal technical domains:

### Domain A — Lossless File Compression

```text
Files
  ↓
File Service
  ↓
Compression Strategy
  ↓
RLE / Huffman / LZW / STORE
  ↓
Bitstream / Serialization
  ↓
FCMP Archive
  ↓
Integrity Metadata
```

### Domain B — Image Optimization

```text
Image
  ↓
Image Loader
  ↓
Format / Mode Selection
  ↓
Quality or Target-Size Optimizer
  ↓
Pillow Encoder
  ↓
Optimized Image
  ↓
Metrics / Preview / Download
```

The two domains share infrastructure such as file handling, metrics, validation, and the Streamlit presentation layer, but they must not be incorrectly treated as the same compression mechanism.

---

# 2. Architecture

## 2.1 High-Level Architecture

```text
                         +-----------------------+
                         |      Streamlit UI     |
                         +-----------+-----------+
                                     |
                                     v
                         +-----------------------+
                         | Application Services |
                         +-----------+-----------+
                                     |
               +---------------------+---------------------+
               |                     |                     |
               v                     v                     v
      +----------------+   +--------------------+  +----------------+
      | File Compression|   | Image Optimization |  | Archive /      |
      | Service         |   | Service            |  | Inspection     |
      +--------+--------+   +---------+----------+  +-------+--------+
               |                      |                     |
               v                      v                     v
      +----------------+   +--------------------+  +----------------+
      | Compression     |   | Image Encoder      |  | FCMP Parser / |
      | Strategy        |   | + Target Optimizer |  | Writer         |
      +--------+--------+   +---------+----------+  +-------+--------+
               |                      |                     |
      +--------+--------+             |                     |
      |        |        |             |                     |
      v        v        v             v                     v
    RLE     Huffman    LZW        Pillow              Binary Layer
      |        |        |             |                     |
      +--------+--------+-------------+---------------------+
                                   |
                          +--------------------+
                          | Integrity / Safety |
                          +--------------------+
                                   |
                          +--------------------+
                          | Filesystem Service |
                          +--------------------+
```

---

# 3. Architectural Principles

## 3.1 Separation of Concerns

The Streamlit application must not contain algorithm implementations.

Preferred flow:

```python
UI
  → Application Service
      → Domain Service
          → Algorithm
```

## 3.2 Dependency Direction

Preferred dependency direction:

```text
UI
 ↓
Application
 ↓
Domain / Algorithms
 ↓
Infrastructure
```

Algorithms should remain usable from:

- tests;
- CLI;
- benchmark scripts;
- Streamlit;

without knowing that Streamlit exists.

## 3.3 Interface-Based Algorithms

Use a common algorithm abstraction where helpful.

Conceptually:

```python
class CompressionAlgorithm:
    name: str

    def compress(self, data: bytes) -> CompressionResult:
        ...

    def decompress(self, payload: bytes, metadata: bytes) -> bytes:
        ...
```

The exact interface may be improved during implementation.

---

# 4. Recommended Project Structure

```text
file-compressor/
│
├── app.py
├── requirements.txt
├── README.md
├── IMPLEMENTATION_PLAN.md
├── pyproject.toml
│
├── ui/
│   ├── __init__.py
│   ├── layout.py
│   ├── general_compression.py
│   ├── image_compression.py
│   ├── target_size.py
│   ├── decompression.py
│   ├── archive_inspector.py
│   ├── benchmark.py
│   └── components.py
│
├── application/
│   ├── __init__.py
│   ├── compression_service.py
│   ├── decompression_service.py
│   ├── image_service.py
│   ├── archive_service.py
│   └── benchmark_service.py
│
├── algorithms/
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── rle.py
│   ├── huffman.py
│   └── lzw.py
│
├── image/
│   ├── __init__.py
│   ├── compressor.py
│   ├── optimizer.py
│   ├── profiles.py
│   ├── formats.py
│   └── metadata.py
│
├── archive/
│   ├── __init__.py
│   ├── format.py
│   ├── writer.py
│   ├── reader.py
│   ├── models.py
│   └── version.py
│
├── binary/
│   ├── __init__.py
│   ├── bit_reader.py
│   ├── bit_writer.py
│   ├── reader.py
│   ├── writer.py
│   └── serialization.py
│
├── integrity/
│   ├── __init__.py
│   └── hashing.py
│
├── filesystem/
│   ├── __init__.py
│   ├── manager.py
│   ├── paths.py
│   └── security.py
│
├── models/
│   ├── __init__.py
│   ├── compression.py
│   ├── image.py
│   ├── archive.py
│   └── metrics.py
│
├── benchmarks/
│   ├── benchmark_algorithms.py
│   ├── benchmark_images.py
│   └── datasets/
│
└── tests/
    ├── unit/
    │   ├── algorithms/
    │   ├── binary/
    │   ├── archive/
    │   ├── image/
    │   ├── integrity/
    │   └── filesystem/
    │
    ├── integration/
    ├── security/
    ├── image/
    └── property/
```

The final structure may be simplified when implementation shows a file/folder is unnecessary.

---

# 5. Technology Stack

## Required

- Python 3.12+
- Streamlit
- Pillow
- pytest

## Standard Library

Prefer standard library components for:

- `pathlib`
- `struct`
- `io`
- `hashlib`
- `heapq`
- `dataclasses`
- `enum`
- `logging`
- `tempfile`
- `time`
- `statistics`
- `argparse` if CLI is included

## Optional Development Tools

- Hypothesis
- psutil
- mypy
- Ruff

Do not add dependencies without a specific purpose.

---

# 6. Core Data Models

Create strongly typed internal models.

Recommended conceptual entities:

```text
CompressionResult
- original_size
- compressed_size
- algorithm
- payload
- metadata
- duration

ArchiveEntry
- path
- original_size
- compressed_size
- algorithm
- metadata
- hash
- payload_offset

ImageCompressionResult
- original_size
- final_size
- format
- quality
- target_size
- target_achieved
- iterations
- duration
- output_bytes
```

Use immutable/frozen dataclasses where appropriate.

---

# 7. Binary Layer

The binary layer is foundational.

Implement:

- bit-level writing;
- bit-level reading;
- unsigned integer serialization;
- fixed-width fields;
- variable-length metadata where the format requires it;
- byte alignment;
- bounds validation;
- end-of-stream checks.

## BitWriter Requirements

Support:

- writing individual bits;
- writing bit sequences;
- flushing partial bytes;
- returning final bytes;
- tracking bit count.

## BitReader Requirements

Support:

- reading individual bits;
- reading N bits;
- detecting exhausted payloads;
- validating requested bit counts.

Special test cases:

```text
0 bits
1 bit
7 bits
8 bits
9 bits
arbitrary non-byte-aligned streams
```

---

# 8. RLE Implementation

Implement RLE on bytes.

Required:

```text
compress(data: bytes) -> payload + metadata
decompress(payload, metadata) -> bytes
```

Handle:

- empty input;
- one byte;
- long runs;
- maximum representable run length;
- alternating bytes;
- all-256-byte values;
- malformed encoded runs.

Do not create ambiguous encodings.

The encoded representation must be documented.

---

# 9. Huffman Implementation

Implement a complete Huffman pipeline.

## Compression

```text
Input bytes
    ↓
Frequency table
    ↓
Priority queue
    ↓
Huffman tree
    ↓
Code generation
    ↓
Bitstream encoding
```

## Decompression

```text
Bitstream
    ↓
Tree / Canonical Metadata
    ↓
Code traversal
    ↓
Output bytes
```

Required edge cases:

- empty input;
- one unique byte;
- two unique bytes;
- equal frequencies;
- all possible byte values;
- incomplete/corrupt tree metadata;
- invalid bitstreams;
- trailing padding.

Prefer canonical Huffman representation if it simplifies deterministic metadata and archive interoperability within this project. Document the chosen design.

---

# 10. LZW Implementation

Implement byte-oriented LZW or another clearly defined input alphabet.

Required components:

- dictionary initialization;
- forward dictionary building;
- code emission;
- decoder reconstruction;
- dictionary growth;
- code width management if applicable;
- maximum dictionary size or reset policy if selected.

Edge case:

```text
KwKwK
```

must be handled correctly.

Malformed code streams must be rejected rather than producing silent corruption.

---

# 11. STORE Fallback

Compression is not guaranteed to reduce size.

For each archive entry:

```text
if compressed_size >= original_size:
    store original bytes
    algorithm = STORE
else:
    use compressed representation
```

A small configurable threshold may be used if justified, but the policy must be documented.

---

# 12. Compression Strategy

Implement a strategy layer.

Conceptual interface:

```text
CompressionStrategy
    analyze()
    select_algorithm()
    compress()
```

Automatic selection should be deterministic.

Possible MVP process:

```text
Input
 ↓
Candidate pre-analysis
 ↓
Choose plausible algorithms
 ↓
Compress candidates
 ↓
Compare resulting payload sizes
 ↓
Select valid smallest representation
 ↓
Compare against original
 ↓
STORE fallback if necessary
```

If performance becomes a concern, introduce a fast pre-classification mechanism before attempting all candidates.

---

# 13. Custom `.fcmp` File Format

The archive must be binary and versioned.

## 13.1 Suggested High-Level Layout

```text
+-----------------------------+
| Magic                       |
+-----------------------------+
| Version                     |
+-----------------------------+
| Global Flags                |
+-----------------------------+
| Entry Count                 |
+-----------------------------+
| Entry Table / Metadata      |
+-----------------------------+
| Payload Region              |
+-----------------------------+
```

Each entry should contain enough information to decode itself.

Conceptual entry:

```text
+-----------------------------+
| Path Length                 |
| Path                       |
| Algorithm ID               |
| Entry Flags                |
| Original Size              |
| Compressed Size            |
| Metadata Length             |
| Payload Length              |
| SHA-256                     |
| Algorithm Metadata          |
| Payload                     |
+-----------------------------+
```

The exact encoding must be explicitly specified in code and `docs/ARCHIVE_FORMAT.md`.

---

# 14. Archive Versioning

At minimum:

```text
FCMP v1
```

must have a clear identifier.

The reader should:

1. validate the magic;
2. read the version;
3. reject unsupported versions explicitly;
4. avoid interpreting unknown layouts as valid data.

Future format versions must be allowed to coexist with old versions conceptually.

---

# 15. Archive Parser Safety

Never trust archive-provided lengths.

Before allocating or reading:

- validate against remaining file size;
- reject impossible values;
- avoid integer overflow assumptions;
- reject negative/invalid values where applicable;
- reject truncated payloads.

Malformed archives must fail cleanly.

---

# 16. Path Security

Implement a dedicated path-sanitization module.

Before extraction:

1. Parse archive path.
2. Normalize it.
3. Resolve it against the destination directory.
4. Verify that the resolved path remains within the destination.
5. Only then write the file.

Reject:

- absolute paths;
- `..` traversal;
- unsafe normalized paths.

Use `pathlib.Path.resolve()` and containment checks appropriately for the platform.

---

# 17. Integrity

Use SHA-256 for archive entry integrity.

Compression:

```text
raw bytes
  ↓
SHA-256
  ↓
compress
  ↓
store digest
```

Extraction:

```text
payload
  ↓
decompress
  ↓
SHA-256
  ↓
compare stored digest
```

Expose status:

```text
VALID
CORRUPTED
UNVERIFIED
```

Do not silently overwrite a valid output with data that fails integrity validation.

---

# 18. Image Compression Architecture

Image compression is separate from the lossless archive algorithms.

Use Pillow for:

- image loading;
- format conversion where appropriate;
- encoding;
- quality settings;
- optimization flags;
- metadata handling.

Do not claim that RLE/Huffman/LZW are performing JPEG/WebP visual quality compression.

---

# 19. Image Compression Profiles

Define configurable profile objects.

Conceptually:

```python
EXTREME
RECOMMENDED
LESS_COMPRESSION
```

Each profile should define values such as:

```text
quality range
preferred formats
optimization flags
metadata policy
```

Do not scatter magic numbers throughout UI code.

---

# 20. Image Format Strategy

Implement an explicit image-output policy.

For example:

### JPEG input

Potentially preserve JPEG or convert to WebP when advantageous.

### PNG input

Preserve PNG where lossless transparency matters, or offer a deliberate conversion path to WebP.

### WebP input

Optimize within WebP when appropriate.

The exact policy must be deterministic and documented.

Avoid silent format changes that surprise the user.

---

# 21. Transparency Handling

For RGBA/transparent images:

- do not accidentally discard alpha;
- do not blindly convert transparent images to JPEG;
- preserve transparency unless the user explicitly chooses a representation that removes it.

When conversion from RGBA to a format without alpha is necessary, require an explicit background policy.

---

# 22. Image Metadata

Provide a setting:

```text
Preserve metadata
```

When enabled:

- preserve supported metadata that can safely be retained;
- maintain orientation correctly.

When disabled:

- remove unnecessary metadata to reduce size where appropriate.

The exact metadata behavior should be documented because not every metadata field can be preserved across format conversions.

---

# 23. Target-Size Optimizer

The target-size optimizer is a core technical feature.

Recommended interface:

```python
optimize(
    image,
    target_size_bytes,
    settings
) -> ImageCompressionResult
```

## Optimization objective

Maximize:

```text
quality
```

subject to:

```text
encoded_size <= target_size_bytes
```

and:

```text
quality >= minimum_quality
```

when such a minimum is configured.

---

# 24. Binary Search Algorithm

For encoders where increasing the quality parameter generally increases output size, use bounded binary search.

Pseudo-process:

```text
low = MIN_QUALITY
high = MAX_QUALITY
best = None

while low <= high and iterations < MAX_ITERATIONS:

    quality = (low + high) // 2

    candidate = encode(image, quality)
    size = len(candidate)

    if size <= target:
        best = candidate
        best_quality = quality
        low = quality + 1
    else:
        high = quality - 1
```

After search:

```text
if best exists:
    return best
else:
    perform defined minimum-quality fallback
```

Do not assume monotonicity across arbitrary format switches. Keep format selection separate from quality search.

---

# 25. Target Size Parameters

Recommended configurable constants:

```text
MIN_QUALITY
MAX_QUALITY
MAX_ITERATIONS
TARGET_TOLERANCE_BYTES
MIN_ACCEPTABLE_QUALITY
```

Avoid hard-coding these throughout the implementation.

Suggested initial search bounds:

```text
1 <= quality <= 100
```

Tune through benchmarks.

---

# 26. Target Size Tolerance

The final requirement is:

```text
final_size <= target_size
```

A result slightly under the target is acceptable.

If the encoder produces a result significantly below target, the optimizer should continue searching for a higher-quality valid result.

The goal is not:

```text
minimum size
```

but:

```text
maximum valid quality under the size constraint
```

---

# 27. Target Size Failure Modes

### Case A — Target smaller than minimum viable representation

Return a clear status:

```text
TARGET_UNACHIEVABLE
```

along with the best candidate, if appropriate.

### Case B — Target larger than source

Do not degrade the image simply to satisfy an unnecessarily large target.

### Case C — Target is close to current size

Search normally and preserve quality.

### Case D — Search limit reached

Return the best valid candidate found and report iteration status.

---

# 28. Candidate Result Model

The optimizer should retain candidate metadata internally:

```text
quality
format
size_bytes
encoded_bytes
```

Do not keep every large encoded candidate indefinitely.

At most, retain:

- current candidate;
- best valid candidate;
- optionally the previous candidate.

---

# 29. Streamlit Frontend

Use Streamlit as the only primary UI framework.

Entry point:

```text
app.py
```

Possible navigation:

```text
General Compression
Image Compression
Target Size
Decompress
Archive Inspector
Benchmarks
```

---

# 30. General Compression UI

Required components:

- file uploader;
- compression mode;
- algorithm selection (`Automatic`, `RLE`, `Huffman`, `LZW`);
- compress button;
- progress;
- results;
- download button.

Example conceptual UI:

```text
Upload files
[ Browse files ]

Compression algorithm
[ Automatic ▼ ]

[ COMPRESS ]

Original size:   12.4 MB
Final size:       4.7 MB
Reduction:       62.1%
Algorithm:       HUFFMAN

[ Download .fcmp ]
```

---

# 31. Image Compression UI

The UI must include three visually distinct selectable cards/options corresponding to:

```text
EXTREME COMPRESSION
Lower quality, maximum compression

RECOMMENDED COMPRESSION
Good quality, good compression

LESS COMPRESSION
Higher quality, lower compression
```

Recommended mode should be selected by default.

The selected mode should have a clear visual indicator such as a check icon, highlight, border, or equivalent Streamlit-friendly styling.

---

# 32. Target Size UI

Provide:

```text
Target Size
[ numeric input ] [ KB / MB ]
```

and:

```text
[ OPTIMIZE & COMPRESS ]
```

During processing display:

```text
Target
Current size
Current quality
Iteration
Progress
```

At completion:

```text
Target Size
Final Size
Final Quality
Reduction
Target Achieved
Optimization Time
```

---

# 33. Before / After Preview

Use Streamlit image rendering to show:

```text
Original
Compressed
```

side by side where practical.

For large images, avoid retaining unnecessary duplicate full-resolution copies.

---

# 34. Download Behavior

Provide:

- download of compressed image;
- download of `.fcmp` archive;
- extracted file downloads when practical.

Downloaded filenames should be deterministic and conflict-safe.

---

# 35. Streamlit State Management

Use `st.session_state` for:

- selected mode;
- uploaded-file metadata;
- current results;
- settings;
- status.

Avoid keeping large byte arrays in persistent session state when unnecessary.

Use temporary files or short-lived in-memory buffers appropriately.

---

# 36. Application Service Layer

The UI should call service functions such as:

```text
compress_files(...)
decompress_archive(...)
inspect_archive(...)
compress_image(...)
optimize_image_to_target(...)
benchmark_algorithms(...)
```

These services should orchestrate domain operations but not contain presentation logic.

---

# 37. Filesystem Service

The filesystem layer should handle:

- input discovery;
- temporary files;
- output files;
- path validation;
- directory creation;
- cleanup.

Use:

```python
pathlib.Path
```

rather than string-based path manipulation.

---

# 38. Temporary Storage

Temporary operations should use controlled temporary directories.

Requirements:

- unique temporary workspace;
- cleanup after completion/failure;
- no accidental deletion of user files;
- no permanent growth from abandoned temporary data.

---

# 39. Logging

Use Python's `logging`.

Recommended levels:

```text
INFO
DEBUG
WARNING
ERROR
```

Examples:

```text
INFO Starting compression
INFO Selected algorithm: HUFFMAN
INFO Original size: 5242880
INFO Compressed size: 1421832
INFO Compression completed in 1.87s
```

Do not log file contents or sensitive metadata unnecessarily.

---

# 40. Error Model

Define application-specific exception types where helpful:

```text
ArchiveFormatError
UnsupportedAlgorithmError
CorruptPayloadError
IntegrityError
UnsafePathError
CompressionError
ImageOptimizationError
```

User-facing messages should be concise and understandable.

Developer logs may contain more diagnostic detail.

---

# 41. CLI

A CLI is optional but recommended for testing and automation.

Suggested operations:

```bash
fcmp compress input.txt -o output.fcmp
fcmp decompress output.fcmp -o extracted/
fcmp inspect output.fcmp
fcmp benchmark input.txt
```

The CLI and Streamlit UI should share application services.

---

# 42. Benchmarking

Create repeatable benchmark scripts.

For general compression record:

```text
Input
Algorithm
Original size
Compressed size
Reduction %
Compression ratio
Compression time
Decompression time
Throughput
```

For image optimization record:

```text
Input
Input format
Output format
Original size
Target size
Final size
Quality
Iterations
Optimization time
Reduction %
```

Do not store fabricated results in the repository as if they were real.

---

# 43. Benchmark Dataset Categories

Use representative data:

### Text

- plain text;
- source code;
- JSON;
- CSV;
- logs.

### Binary

- random data;
- structured binary.

### Already Compressed

- JPEG;
- PNG;
- WebP;
- PDF;
- ZIP if used as a test input.

### Images

- photographs;
- screenshots;
- illustrations;
- transparent graphics;
- grayscale images;
- low-resolution images;
- high-resolution images.

---

# 44. Testing Strategy

Use multiple testing levels.

## Unit

Every algorithm and infrastructure component must have isolated tests.

## Integration

Test:

```text
input → compress → archive → read → decompress → hash comparison
```

## Property-Based

For valid random byte sequences:

```text
decompress(compress(data)) == data
```

## Corruption

Modify:

- header;
- metadata;
- payload;
- lengths;
- checksum;
- version.

Expected result:

```text
clean failure
```

## Security

Test:

- `../`;
- absolute paths;
- Windows path traversal;
- malformed lengths;
- invalid algorithm identifiers.

---

# 45. Image Tests

Test:

- JPEG;
- PNG;
- WebP;
- RGB;
- RGBA;
- grayscale;
- transparency;
- metadata on/off;
- very small files;
- large files.

Target-size tests must verify:

```text
result_size <= target
```

whenever the configured quality constraints make the target achievable.

Also verify:

```text
higher valid quality is preferred
```

when multiple valid candidates exist.

---

# 46. Target Size Optimizer Tests

Example logical test:

```text
Candidate A:
quality = 70
size = 900 KB

Candidate B:
quality = 80
size = 980 KB

Target = 1 MB
```

Expected:

```text
quality = 80
```

because it is the highest valid quality candidate.

Another test:

```text
Candidate:
quality = 90
size = 1.4 MB

Target:
1 MB
```

The optimizer must continue searching rather than returning the oversized candidate.

---

# 47. Performance and Memory Requirements

Avoid:

- unnecessary full-file copies;
- repeated reads from disk;
- repeated image decoding;
- excessive candidate retention;
- quadratic dictionary behavior where avoidable.

For very large inputs, the architecture should permit later streaming.

The MVP may still use in-memory processing for some algorithms when that significantly simplifies implementation, but this limitation must be documented.

---

# 48. Security Requirements

All archive fields originating from disk must be considered untrusted.

Validate:

```text
magic
version
flags
entry_count
path_length
metadata_length
compressed_size
original_size
payload_boundaries
algorithm_id
hash length
```

Do not trust an archive's claimed size.

Before allocating large structures based on metadata, validate values against sensible bounds and available data.

---

# 49. Data Integrity Requirements

For every archive entry:

```text
hash(original_bytes) == stored_hash
```

after successful decompression.

A successful extraction must mean:

1. payload decoded;
2. expected byte count satisfied;
3. integrity verified.

---

# 50. Output Conflict Policy

When extracting to an existing directory, support a deterministic policy such as:

```text
ASK / OVERWRITE / SKIP / RENAME
```

The default should avoid accidental data loss.

For the Streamlit UI, a simple safe default such as rename or skip is preferable for the MVP.

---

# 51. Configuration

Centralize application constants.

Possible structure:

```text
config.py

ARCHIVE_VERSION
MAX_ARCHIVE_ENTRIES
MAX_METADATA_SIZE
TARGET_SIZE_MAX_ITERATIONS
MIN_IMAGE_QUALITY
MAX_IMAGE_QUALITY
DEFAULT_IMAGE_PROFILE
```

Avoid scattered literals.

---

# 52. Documentation Requirements

The repository must include:

```text
README.md
docs/ARCHITECTURE.md
docs/ALGORITHMS.md
docs/ARCHIVE_FORMAT.md
docs/IMAGE_OPTIMIZATION.md
docs/TESTING.md
```

Documentation must explain both:

- how to use the product;
- how the implementation works.

---

# 53. Code Quality Requirements

Use:

- type hints;
- docstrings for public functions/classes;
- descriptive identifiers;
- focused modules;
- explicit exceptions;
- deterministic behavior;
- unit-testable components.

Avoid:

- giant functions;
- circular imports;
- UI/business-logic mixing;
- hidden global state;
- broad exception swallowing;
- duplicated serialization logic.

---

# 54. Extensibility

New algorithms should be addable through an algorithm registry.

Conceptual flow:

```text
Algorithm Registry
 ├── RLE
 ├── HUFFMAN
 ├── LZW
 ├── STORE
 └── Future Algorithm
```

The archive should store a stable algorithm identifier.

Adding a new algorithm should not require modifications to:

- archive parsing architecture;
- Streamlit navigation;
- integrity system.

Only the algorithm registry, implementation, and relevant tests/metadata should need significant changes.

---

# 55. Implementation Phases

Recommended dependency order:

## Phase 1
Project configuration and repository inspection.

## Phase 2
Data models and binary primitives.

## Phase 3
RLE.

## Phase 4
Huffman.

## Phase 5
LZW.

## Phase 6
Algorithm registry and automatic selection.

## Phase 7
FCMP archive writer/reader.

## Phase 8
Integrity and secure extraction.

## Phase 9
General file application services.

## Phase 10
Image loading and encoding.

## Phase 11
Image compression profiles.

## Phase 12
Target-size optimizer.

## Phase 13
Streamlit UI.

## Phase 14
Batch operations.

## Phase 15
Testing, security validation, and corruption testing.

## Phase 16
Benchmarking and performance tuning.

## Phase 17
Documentation and UX polish.

---

# 56. Definition of Done

A component is considered done when:

```text
[ ] Implementation complete
[ ] Unit tests exist
[ ] Edge cases covered
[ ] Integration behavior verified
[ ] Errors handled
[ ] Logging appropriate
[ ] Documentation updated
```

The project is complete when all MVP acceptance criteria in the PRD are satisfied.

---

# 57. Technical Acceptance Criteria

```text
[ ] Python project installs from a clean environment
[ ] Streamlit app launches successfully
[ ] RLE compression/decompression passes all tests
[ ] Huffman compression/decompression passes all tests
[ ] LZW compression/decompression passes all tests
[ ] STORE fallback works
[ ] FCMP writer/reader round-trip works
[ ] Multi-file archive works
[ ] Metadata is validated
[ ] SHA-256 integrity works
[ ] Corruption is detected
[ ] Path traversal is blocked
[ ] Image compression works
[ ] Three image profiles work
[ ] Target-size optimization works
[ ] Binary-search/bounded optimization is used
[ ] Highest valid quality is selected
[ ] Target failure is reported honestly
[ ] Progress is shown for long operations
[ ] Real metrics are displayed
[ ] Tests pass
[ ] Benchmarks execute
[ ] Documentation is complete
```

---

# 58. Example Service-Level Interfaces

These are conceptual and should be refined during implementation.

```python
def compress_files(
    files: list[Path],
    algorithm: str = "auto"
) -> CompressionResult:
    ...

def decompress_archive(
    archive_path: Path,
    output_dir: Path
) -> ExtractionResult:
    ...

def inspect_archive(
    archive_path: Path
) -> ArchiveInspection:
    ...

def compress_image(
    image_bytes: bytes,
    profile: str
) -> ImageCompressionResult:
    ...

def optimize_image_to_target(
    image_bytes: bytes,
    target_size_bytes: int,
    settings: TargetSizeSettings
) -> ImageCompressionResult:
    ...
```

Keep these independent of Streamlit.

---

# 59. Example Target Optimization Contract

Input:

```text
image
target_size_bytes
minimum_quality
maximum_quality
maximum_iterations
output_format
```

Output:

```text
output_bytes
final_size_bytes
final_quality
target_achieved
iterations
duration
format
```

The service must never claim:

```text
target_achieved = True
```

unless:

```text
final_size_bytes <= target_size_bytes
```

---

# 60. Important Technical Distinction

The following must never be conflated:

```text
RLE / Huffman / LZW
        =
lossless data compression algorithms
```

versus:

```text
JPEG / WebP quality encoding
        =
image representation/optimization with potential quality loss
```

The architecture, documentation, and UI should all preserve this distinction.

---

# 61. Final Engineering Principle

The application should be built as a serious software system rather than a collection of demos.

The desired outcome is:

```text
Algorithmic Depth
      +
Binary Systems Engineering
      +
Custom Archive Design
      +
Image Optimization
      +
Target-Size Search
      +
Streamlit UX
      +
Security
      +
Testing
      +
Benchmarking
```

The project should be understandable from source code, reproducible from a clean environment, and credible as a substantial portfolio/research/academic engineering project.
