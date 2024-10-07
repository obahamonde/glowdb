import { v4 as uuidv4 } from 'uuid';

type GlowMethod =
  | "CreateTable"
  | "DeleteTable"
  | "GetItem"
  | "PutItem"
  | "UpdateItem"
  | "DeleteItem"
  | "Scan"
  | "Query"
  | "BatchGetItem"
  | "BatchWriteItem";

interface RPCRequest<P = any> {
  rpc_version: "2.0";
  method: GlowMethod;
  params: P;
  id: string;
}

interface RPCResponse<R = any> {
  jsonrpc: "2.0";
  result?: R;
  error?: {
    message: string;
    code: number;
  };
  id: string;
}

class RPCError extends Error {
  code: number;

  constructor(message: string, code: number) {
    super(message);
    this.code = code;
    this.name = 'RPCError';
  }
}

export abstract class DocumentObject {
  id: string;
  object: string;

  constructor(data: any) {
    this.id = data.id || `${this.constructor.name.toLowerCase()}_${uuidv4()}`;
    this.object = this.constructor.name.toLowerCase();
  }

  toJSON(): Record<string, any> {
    return Object.entries(this).reduce((acc, [key, value]) => {
      if (value !== undefined) {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, any>);
  }
}

export class GlowDBClient<D extends DocumentObject> {
  private ws: WebSocket | null = null;
  private url: string;
  private modelType: new (data: any) => D;
  private requestQueue: Map<string, { resolve: (value: any) => void, reject: (reason: any) => void }> = new Map();

  constructor(modelType: new (data: any) => D, url: string = "ws://localhost:8888") {
    this.url = url;
    this.modelType = modelType;
    console.debug("GlowDBClient initialized");
    console.debug("URL:", this.url);
    console.debug("Model type:", this.modelType.name);
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => {
        console.debug("Connected to", this.url);
        this.setupMessageHandler();
        resolve();
      };
      this.ws.onerror = (error) => reject(error);
    });
  }

  private setupMessageHandler() {
    if (!this.ws) return;
    this.ws.onmessage = (event) => {
      const response: RPCResponse = JSON.parse(event.data);
      const requestId = response.id;
      const pendingRequest = this.requestQueue.get(requestId);
      if (pendingRequest) {
        if (response.error) {
          pendingRequest.reject(new RPCError(response.error.message, response.error.code));
        } else {
          pendingRequest.resolve(response.result);
        }
        this.requestQueue.delete(requestId);
      }
    };
  }

  async close(): Promise<void> {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      console.debug("Disconnected from", this.url);
    }
  }

  private async request<P = any, R = any>(method: GlowMethod, params: P): Promise<R> {
    if (!this.ws) {
      await this.connect();
    }
    if (!this.ws) throw new Error("WebSocket is not connected");

    return new Promise((resolve, reject) => {
      const requestId = uuidv4();
      const request: RPCRequest<P> = {
        rpc_version: "2.0",
        method,
        params,
        id: requestId,
      };

      this.requestQueue.set(requestId, { resolve, reject });
      this.ws.send(JSON.stringify(request));
    });
  }

  async createTable(tableName: string): Promise<void> {
    await this.request<{ table_name: string }, void>("CreateTable", { table_name: tableName });
  }

  async deleteTable(tableName: string): Promise<void> {
    await this.request<{ table_name: string }, void>("DeleteTable", { table_name: tableName });
  }

  async getItem(tableName: string, id: string): Promise<D> {
    const result = await this.request<{ table_name: string; id: string }, any>("GetItem", { table_name: tableName, id });
    return new this.modelType(result);
  }

  async putItem(tableName: string, document: D): Promise<D> {
    const result = await this.request<{ table_name: string; document: Record<string, any> }, any>(
      "PutItem",
      { table_name: tableName, document: document.toJSON() }
    );
    return new this.modelType(result);
  }

  async updateItem(tableName: string, id: string, updates: Partial<D>): Promise<D> {
    const result = await this.request<{ table_name: string; id: string; updates: Partial<D> }, any>(
      "UpdateItem",
      { table_name: tableName, id, updates }
    );
    return new this.modelType(result);
  }

  async deleteItem(tableName: string, id: string): Promise<void> {
    await this.request<{ table_name: string; id: string }, void>("DeleteItem", { table_name: tableName, id });
  }

  async scan(tableName: string): Promise<D[]> {
    const result = await this.request<{ table_name: string }, any[]>("Scan", { table_name: tableName });
    return result.map(item => new this.modelType(item));
  }

  async query(tableName: string, limit: number = 25, offset: number = 0, filters?: Record<string, any>): Promise<D[]> {
    const result = await this.request<{ table_name: string; limit: number; offset: number; filters?: Record<string, any> }, any[]>(
      "Query",
      { table_name: tableName, limit, offset, filters }
    );
    return result.map(item => new this.modelType(item));
  }

  async batchGetItem(tableName: string, ids: string[]): Promise<D[]> {
    const result = await this.request<{ table_name: string; ids: string[] }, any[]>(
      "BatchGetItem",
      { table_name: tableName, ids }
    );
    return result.map(item => new this.modelType(item));
  }

  async batchWriteItem(tableName: string, items: D[]): Promise<D[]> {
    const result = await this.request<{ table_name: string; items: Record<string, any>[] }, any[]>(
      "BatchWriteItem",
      { table_name: tableName, items: items.map(item => item.toJSON()) }
    );
    return result.map(item => new this.modelType(item));
  }
}