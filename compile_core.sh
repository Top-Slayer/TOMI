nuitka core-process/core.py \
  --follow-imports \
  --lto=no \
  --clang \
  --jobs=$(nproc) \
  --remove-output \
  --enable-plugin=no-qt