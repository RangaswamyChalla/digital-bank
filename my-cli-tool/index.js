#!/usr/bin/env node
import { Command } from 'commander';
import { Ollama } from 'ollama';

const program = new Command();

const ollama = new Ollama({ host: 'http://localhost:11434' });

program
  .name('my-cli')
  .description('AI-powered CLI using local Ollama')
  .version('1.0.0');

program
  .command('ask <prompt>')
  .description('Ask the AI a question')
  .option('-m, --model <model>', 'model to use', 'llama3.2')
  .action(async (prompt, options) => {
    console.log(`\nAsking ${options.model}...\n`);

    try {
      const response = await ollama.chat({
        model: options.model,
        messages: [{ role: 'user', content: prompt }],
        stream: true,
      });

      for await (const part of response) {
        process.stdout.write(part.message.content);
      }
      console.log('\n');
    } catch (error) {
      console.error(`Error: ${error.message}`);
      console.error('Make sure Ollama is running at http://localhost:11434');
      process.exit(1);
    }
  });

program.parse();
