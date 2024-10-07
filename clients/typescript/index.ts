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
	jsonrpc: "2.0";
	method: GlowMethod;
	params: P;
	id: string;
}

interface RPCResponse<R = any> {
	jsonrpc: "2.0";
	result?: R;
	error?: {
		code: number;
		message: string;
	};
	id: string;
}

export class DocumentObject {
	id: string;
	[key: string]: any;

	constructor(data: any) {
		this.id = data.id || uuidv4();
		Object.assign(this, data);
	}

	get object(): string {
		return this.constructor.name.toLowerCase();
	}
}

export class RPCClient<O extends DocumentObject> {
	private ws: WebSocket | null = null;
	private uri: string;
	private model: new (data: any) => O;

	constructor(uri: string = "ws://localhost:8888", model: new (data: any) => O) {
		this.uri = uri;
		this.model = model;
	}

	async connect(): Promise<void> {
		return new Promise((resolve, reject) => {
			this.ws = new WebSocket(this.uri);
			this.ws.onopen = () => resolve();
			this.ws.onerror = (error) => reject(error);
		});
	}

	async close(): Promise<void> {
		if (this.ws) {
			this.ws.close();
			this.ws = null;
		}
	}

	private async sendRequest<P = any, R = any>(method: GlowMethod, params: P): Promise<R> {
		if (!this.ws) {
			throw new Error("Not connected to the server");
		}

		return new Promise((resolve, reject) => {
			const request: RPCRequest<P> = {
				jsonrpc: "2.0",
				method,
				params,
				id: uuidv4(),
			};

			const handleMessage = (event: MessageEvent) => {
				const response: RPCResponse<R> = JSON.parse(event.data);
				if (response.id === request.id) {
					this.ws!.removeEventListener('message', handleMessage);
					if (response.error) {
						reject(new Error(`Error ${response.error.code}: ${response.error.message}`));
					} else {
						resolve(response.result!);
					}
				}
			};

			this.ws.addEventListener('message', handleMessage);
			this.ws.send(JSON.stringify(request));
		});
	}

	async createTable(tableName: string): Promise<any> {
		return this.sendRequest("CreateTable", { table_name: tableName });
	}

	async deleteTable(tableName: string): Promise<any> {
		return this.sendRequest("DeleteTable", { table_name: tableName });
	}

	async putItem(tableName: string, item: O): Promise<any> {
		return this.sendRequest("PutItem", { table_name: tableName, item });
	}

	async getItem(tableName: string, id: string): Promise<O> {
		const result = await this.sendRequest<{ table_name: string; id: string }, any>("GetItem", { table_name: tableName, id });
		return new this.model(result);
	}

	async updateItem(tableName: string, id: string, updates: Partial<O>): Promise<any> {
		return this.sendRequest("UpdateItem", { table_name: tableName, id, updates });
	}

	async deleteItem(tableName: string, id: string): Promise<any> {
		return this.sendRequest("DeleteItem", { table_name: tableName, id });
	}

	async scan(tableName: string, limit: number = 25, offset: number = 0): Promise<O[]> {
		const result = await this.sendRequest<{ table_name: string; limit: number; offset: number }, any[]>(
			"Scan",
			{ table_name: tableName, limit, offset }
		);
		return result.map(item => new this.model(item));
	}

	async query(tableName: string, filters?: Record<string, any>, limit: number = 25, offset: number = 0): Promise<O[]> {
		const params: any = { table_name: tableName, limit, offset };
		if (filters) {
			params.filters = filters;
		}
		const result = await this.sendRequest<typeof params, any[]>("Query", params);
		return result.map(item => new this.model(item));
	}

	async batchGetItem(ids: string[], tableName: string): Promise<O[]> {
		const result = await this.sendRequest<{ table_name: string; ids: string[] }, any[]>(
			"BatchGetItem",
			{ table_name: tableName, ids }
		);
		return result.map(item => new this.model(item));
	}

	async batchWriteItem(items: O[], tableName: string): Promise<any> {
		return this.sendRequest("BatchWriteItem", { table_name: tableName, items });
	}
}

// Example usage:
class ExampleDocument extends DocumentObject {
	name: string;
	value: number;

	constructor(data: any) {
		super(data);
		this.name = data.name;
		this.value = data.value;
	}
}

async function main() {
	const client = new RPCClient<ExampleDocument>("ws://localhost/rpc", ExampleDocument);

	try {
		await client.connect();

		await client.createTable("chicho");

		const newItem = new ExampleDocument({ name: "Test Item", value: 42 });
		await client.putItem("chicho", newItem);

		const retrievedItem = await client.getItem("chicho", newItem.id);
		console.log("Retrieved item:", retrievedItem);

		await client.close();
	} catch (error) {
		console.error("An error occurred:", error);
	}
}


main()