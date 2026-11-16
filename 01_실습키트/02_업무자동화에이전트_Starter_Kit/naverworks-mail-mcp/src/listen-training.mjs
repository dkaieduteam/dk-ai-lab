import { createServer } from "node:http";
import { connect } from "node:net";
export const MCP_PORTS = Object.freeze([3000, 58080, 61080]);
const retryable = new Set(["EADDRINUSE", "EACCES", "EADDRNOTAVAIL"]);

// Windows lets 127.0.0.1:port bind even when another program holds 0.0.0.0:port,
// so a successful bind alone does not mean the port is ours. Detect any listener first.
function acceptsConnection(port, host, timeoutMs = 500) {
  return new Promise((resolve) => {
    const socket = connect({ port, host });
    const finish = (busy) => { socket.destroy(); resolve(busy); };
    socket.setTimeout(timeoutMs, () => finish(false));
    socket.once("connect", () => finish(true));
    socket.once("error", () => finish(false));
  });
}

export async function isPortInUse(port) {
  const results = await Promise.all([acceptsConnection(port, "127.0.0.1"), acceptsConnection(port, "::1")]);
  return results.some(Boolean);
}

// Bind in the server itself; an availability probe cannot reserve a port.
export async function listenTraining(app, ports = MCP_PORTS, makeServer = createServer, portInUse = isPortInUse) {
  for (const port of ports) {
    if (await portInUse(port)) continue;
    const server = makeServer(app);
    try {
      await new Promise((resolve, reject) => {
        const failed = (error) => reject(error);
        server.once("error", failed);
        server.listen(port, "127.0.0.1", () => {
          server.removeListener("error", failed);
          resolve();
        });
      });
      return server;
    } catch (error) {
      if (!retryable.has(error.code)) throw new Error("MCP_START_FAILED");
    }
  }
  throw new Error("MCP_PORTS_UNAVAILABLE");
}
