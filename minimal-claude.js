#!/usr/bin/env node

const { spawn } = require('child_process');

// 从命令行参数获取问题
const prompt = process.argv[2];

if (!prompt) {
  console.error('用法: node minimal-claude.js "你的问题"');
  process.exit(1);
}

// 启动 Claude CLI 子进程
const claude = spawn('claude', [
  '-p', prompt,
  '--output-format', 'stream-json',
  '--verbose'
], {
  stdio: ['ignore', 'pipe', 'pipe']
});

let fullResponse = '';
let buffer = '';

// 处理 stdout（流式 JSON）
claude.stdout.on('data', (data) => {
  buffer += data.toString();
  
  // 按行分割
  const lines = buffer.split('\n');
  buffer = lines.pop() || ''; // 保留未完成的行
  
  for (const line of lines) {
    if (!line.trim()) continue;
    
    try {
      const event = JSON.parse(line);
      
      // 提取 assistant 消息中的文本
      if (event.type === 'assistant' && event.message?.content) {
        for (const block of event.message.content) {
          if (block.type === 'text') {
            fullResponse += block.text;
          }
        }
      }
      
      // 处理结果事件
      if (event.type === 'result') {
        if (event.subtype === 'success') {
          console.log(fullResponse);
        } else if (event.subtype === 'error') {
          console.error('错误:', event.message || '未知错误');
        }
      }
    } catch (e) {
      // 忽略解析失败的行
    }
  }
});

// 处理 stderr（静默忽略，除非需要调试）
claude.stderr.on('data', () => {});

// 处理进程退出
claude.on('close', (code) => {
  process.exit(code || 0);
});

// 处理错误
claude.on('error', (err) => {
  console.error('启动 Claude CLI 失败:', err.message);
  process.exit(1);
});