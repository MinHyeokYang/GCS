#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

function toJsonText(obj) {
  return JSON.stringify(obj, null, 2);
}

function getBaseUrl() {
  return (process.env.GCS_PULSE_API_BASE_URL || "https://api.1000.school").replace(/\/+$/, "");
}

function getToken() {
  return process.env.GCS_PULSE_TOKEN || process.env.ANTHROPIC_AUTH_TOKEN || "";
}

async function callApi(method, path, body) {
  const token = getToken();
  if (!token) {
    throw new Error("Missing token. Set GCS_PULSE_TOKEN or ANTHROPIC_AUTH_TOKEN.");
  }

  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const started = Date.now();
  const response = await fetch(`${getBaseUrl()}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const elapsedMs = Date.now() - started;

  const text = await response.text();
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    parsed = { raw: text };
  }

  if (!response.ok) {
    const err = new Error(`HTTP ${response.status}`);
    err.details = { status: response.status, elapsed_ms: elapsedMs, body: parsed };
    throw err;
  }

  return {
    status: response.status,
    elapsed_ms: elapsedMs,
    data: parsed,
  };
}

const server = new Server(
  { name: "gcs-pulse-mcp-bridge", version: "0.2.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "list_meeting_rooms",
      description: "List all meeting rooms from api.1000.school",
      inputSchema: {
        type: "object",
        properties: {},
        additionalProperties: false,
      },
    },
    {
      name: "list_room_reservations",
      description: "List reservations for one room on a date (YYYY-MM-DD).",
      inputSchema: {
        type: "object",
        properties: {
          room_id: { type: "integer" },
          date: { type: "string" },
        },
        required: ["room_id", "date"],
        additionalProperties: false,
      },
    },
    {
      name: "create_room_reservation",
      description: "Create a meeting-room reservation.",
      inputSchema: {
        type: "object",
        properties: {
          room_id: { type: "integer" },
          start_at: { type: "string" },
          end_at: { type: "string" },
          purpose: { type: "string" },
        },
        required: ["room_id", "start_at", "end_at"],
        additionalProperties: false,
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const name = req.params.name;
  const args = req.params.arguments ?? {};

  try {
    if (name === "list_meeting_rooms") {
      const result = await callApi("GET", "/meeting-rooms");
      return { content: [{ type: "text", text: toJsonText(result) }] };
    }

    if (name === "list_room_reservations") {
      const roomId = Number(args.room_id);
      const date = String(args.date || "");
      if (!roomId || !date) {
        throw new Error("room_id and date are required");
      }
      const result = await callApi(
        "GET",
        `/meeting-rooms/${roomId}/reservations?date=${encodeURIComponent(date)}`
      );
      return { content: [{ type: "text", text: toJsonText(result) }] };
    }

    if (name === "create_room_reservation") {
      const roomId = Number(args.room_id);
      const startAt = String(args.start_at || "");
      const endAt = String(args.end_at || "");
      const purpose = args.purpose == null ? undefined : String(args.purpose);
      if (!roomId || !startAt || !endAt) {
        throw new Error("room_id, start_at, end_at are required");
      }
      const body = { start_at: startAt, end_at: endAt };
      if (purpose) {
        body.purpose = purpose;
      }
      const result = await callApi(
        "POST",
        `/meeting-rooms/${roomId}/reservations`,
        body
      );
      return { content: [{ type: "text", text: toJsonText(result) }] };
    }

    return {
      isError: true,
      content: [{ type: "text", text: "Unknown tool name." }],
    };
  } catch (error) {
    const details = error.details || { message: String(error.message || error) };
    return {
      isError: true,
      content: [{ type: "text", text: toJsonText(details) }],
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
