import { GlowDBClient, DocumentObject } from './src/composables/rpc';

// Define your document type
class MyDocument extends DocumentObject {
	// Add your specific fields here
	content: string;

	constructor({ content }: { content: string }) {
		super({ content });  // Pass the content to the parent constructor
		this.content = content;
	}
}

// Create a client instance
const client = new GlowDBClient<MyDocument>(MyDocument, 'ws://localhost:8888');
const { log } = console;
// Use the client
async function example() {

}

example().catch(log);

