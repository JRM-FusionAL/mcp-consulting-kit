FROM python:3.11-slim

RUN apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip "setuptools>=78.1.1" wheel && \
    rm -rf /usr/local/lib/python3.11/ensurepip

WORKDIR /app

COPY business-intelligence-mcp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ ./showcase_servers/common/
RUN touch ./showcase_servers/__init__.py
COPY business-intelligence-mcp/ .

# pip vendors its own internal copies of setuptools and msgpack (see
# site-packages/pip/_vendor/vendor.txt) that lag behind upstream fixed
# versions (CVE-2025-47273, GHSA-6v7p-g79w-8964). Those vendored copies are
# only used by pip's own bootstrap machinery, not importable by app code,
# but Trivy still flags them via pip's bundled SBOM. This is a runtime
# image that never needs pip after dependencies are installed, so remove
# it entirely rather than waive the CVEs.
RUN python -m pip uninstall -y pip && \
    rm -rf /usr/local/lib/python3.11/site-packages/pip* /usr/local/bin/pip*

ENV PORT=8101

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8101", "--forwarded-allow-ips", "*"]
