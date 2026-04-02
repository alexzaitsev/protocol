# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from mcp.types import ToolAnnotations

READ = ToolAnnotations(readOnlyHint=True, idempotentHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, idempotentHint=True)
