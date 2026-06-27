"""Agent Mesh CLI命令行工具"""
import asyncio
import json
import sys
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from rich.prompt import Prompt, Confirm
import websockets

from .agent_client import AgentClient

console = Console()


def run_async(coro):
    """运行异步函数"""
    return asyncio.get_event_loop().run_until_complete(coro)


@click.group()
@click.option('--server', '-s', default='ws://localhost:18800', help='Agent Mesh服务器地址')
@click.pass_context
def cli(ctx, server):
    """Agent Mesh CLI - Agent通信系统命令行工具"""
    ctx.ensure_object(dict)
    ctx.obj['server'] = server


@cli.command()
@click.option('--name', '-n', required=True, help='Agent名称')
@click.option('--type', '-t', 'agent_type', default='custom', help='Agent类型')
@click.option('--id', 'agent_id', help='Agent ID（可选）')
@click.pass_context
def register(ctx, name, agent_type, agent_id):
    """注册新Agent"""
    async def _register():
        with console.status(f"[bold green]正在连接服务器..."):
            client = AgentClient(agent_id or name, name, agent_type)
            if await client.connect(ctx.obj['server']):
                console.print(f"[green]✓[/green] Agent '[bold]{name}[/bold]' 注册成功")
                await client.disconnect()
            else:
                console.print(f"[red]✗[/red] 连接服务器失败")

    run_async(_register())


@cli.command()
@click.option('--json', '-j', is_flag=True, help='JSON格式输出')
@click.pass_context
def agents(ctx, json_output):
    """列出所有Agent"""
    async def _agents():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:18801/api/agents") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        agent_list = data.get('agents', [])
                        if json_output:
                            console.print(json.dumps(agent_list, indent=2, ensure_ascii=False))
                            return
                        if not agent_list:
                            console.print("[dim]暂无已注册Agent[/dim]")
                            return

                        table = Table(title="已注册Agent列表", show_header=True, header_style="bold magenta")
                        table.add_column("名称", style="cyan", width=20)
                        table.add_column("ID", style="dim", width=25)
                        table.add_column("类型", width=12)
                        table.add_column("状态", width=10)
                        table.add_column("能力", width=30)

                        for agent in agent_list:
                            status_color = "[green]" if agent.get('status') == 'online' else "[red]"
                            table.add_row(
                                agent.get('name', ''),
                                agent.get('id', ''),
                                agent.get('type', ''),
                                f"{status_color}{agent.get('status', '')}",
                                ', '.join(agent.get('capabilities', [])[:3]) or '-'
                            )
                        console.print(table)
                        console.print(f"\n[dim]共 {len(agent_list)} 个Agent[/dim]")
                    else:
                        console.print("[red]获取Agent列表失败[/red]")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")

    run_async(_agents())


@cli.command()
@click.option('--from', '-f', 'from_agent', required=True, help='发送者Agent ID')
@click.option('--to', '-t', required=True, help='接收者Agent ID')
@click.option('--message', '-m', required=True, help='消息内容')
@click.pass_context
def send(ctx, from_agent, to, message):
    """发送消息"""
    async def _send():
        with console.status(f"[bold]发送消息中..."):
            client = AgentClient(from_agent, from_agent)
            if await client.connect(ctx.obj['server']):
                success = await client.send_message(to, message)
                if success:
                    console.print(f"[green]✓[/green] 消息已发送: [bold]{from_agent}[/bold] → [bold]{to}[/bold]")
                else:
                    console.print(f"[red]✗[/red] 发送失败")
                await client.disconnect()
            else:
                console.print(f"[red]✗[/red] 连接服务器失败")

    run_async(_send())


@cli.command()
@click.option('--from', '-f', 'from_agent', required=True, help='发送者Agent ID')
@click.option('--to', '-t', required=True, help='接收者Agent ID')
@click.option('--title', required=True, help='任务标题')
@click.option('--description', '-d', default='', help='任务描述')
@click.option('--priority', '-p', type=click.Choice(['high', 'normal', 'low']), default='normal', help='优先级')
@click.pass_context
def task(ctx, from_agent, to, title, description, priority):
    """创建任务"""
    async def _task():
        with console.status(f"[bold]创建任务中..."):
            client = AgentClient(from_agent, from_agent)
            if await client.connect(ctx.obj['server']):
                success = await client.create_task(to, title, description, priority)
                if success:
                    console.print(f"[green]✓[/green] 任务已创建: [bold]{title}[/bold]")
                    console.print(f"[dim]  创建者: {from_agent} → 执行者: {to}[/dim]")
                    console.print(f"[dim]  优先级: {priority}[/dim]")
                else:
                    console.print(f"[red]✗[/red] 创建失败")
                await client.disconnect()
            else:
                console.print(f"[red]✗[/red] 连接服务器失败")

    run_async(_task())


@cli.command()
@click.option('--from', '-f', 'from_agent', required=True, help='发送者Agent ID')
@click.option('--message', '-m', required=True, help='广播消息内容')
@click.option('--target', '-t', default='*', help='目标 (* 或 群组ID)')
@click.pass_context
def broadcast(ctx, from_agent, message, target):
    """广播消息"""
    async def _broadcast():
        with console.status(f"[bold]广播消息中..."):
            client = AgentClient(from_agent, from_agent)
            if await client.connect(ctx.obj['server']):
                success = await client.broadcast(message, target)
                if success:
                    console.print(f"[green]✓[/green] 广播已发送 to [bold]{target}[/bold]")
                else:
                    console.print(f"[red]✗[/red] 发送失败")
                await client.disconnect()
            else:
                console.print(f"[red]✗[/red] 连接服务器失败")

    run_async(_broadcast())


@cli.command()
@click.pass_context
def status(ctx):
    """查看服务器状态"""
    async def _status():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:18801/api/stats") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        console.print(Panel(
                            f"[bold cyan]在线Agent:[/bold cyan] {data.get('online_count', 0)}\n"
                            f"[bold cyan]已注册:[/bold cyan] {data.get('agents', {}).get('confirmed_count', 0)}\n"
                            f"[bold cyan]待确认:[/bold cyan] {data.get('agents', {}).get('pending_count', 0)}\n"
                            f"[bold cyan]消息队列:[/bold cyan] {data.get('queue_size', 0)}\n"
                            f"[bold cyan]活跃任务:[/bold cyan] {data.get('task_count', 0)}",
                            title="[bold]Agent Mesh 状态[/bold]"
                        ))
                    else:
                        console.print("[red]获取状态失败[/red]")
        except Exception:
            try:
                async with websockets.connect(ctx.obj['server']) as ws:
                    console.print("[green]✓[/green] WebSocket服务器运行正常")
            except Exception as e:
                console.print(f"[red]✗[/red] 无法连接: {e}")

    run_async(_status())


@cli.command()
@click.option('--agent', '-a', required=True, help='Agent ID')
@click.pass_context
def history(ctx, agent):
    """查看消息历史"""
    async def _history():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:18801/api/messages/{agent}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        messages = data.get('messages', [])
                        if not messages:
                            console.print("[dim]暂无消息记录[/dim]")
                            return

                        table = Table(title=f"消息历史 - {agent}", show_header=True)
                        table.add_column("时间", style="cyan", width=20)
                        table.add_column("类型", style="magenta", width=12)
                        table.add_column("发送者", style="green", width=15)
                        table.add_column("接收者", style="green", width=15)
                        table.add_column("内容", width=40)

                        for msg in messages:
                            content = str(msg.get('payload', {}).get('text', ''))[:40]
                            table.add_row(
                                (msg.get('timestamp', '') or '')[:19],
                                msg.get('type', ''),
                                msg.get('from', ''),
                                msg.get('to', ''),
                                content
                            )
                        console.print(table)
                    else:
                        console.print("[red]获取历史记录失败[/red]")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")

    run_async(_history())


@cli.command()
@click.option('--agent', '-a', help='Agent ID（留空则监听所有消息）')
@click.pass_context
def listen(ctx, agent):
    """监听消息（交互模式）"""
    async def _listen():
        agent_id = agent or f"listener-{id(asyncio.current_task())}"

        client = AgentClient(agent_id, agent_id)

        # 定义消息处理器
        def on_message(data):
            msg_type = data.get('type')
            if msg_type == 'message':
                from_agent = data.get('from', 'unknown')
                text = data.get('payload', {}).get('text', '')
                console.print(f"\n[blue bold]← 来自 {from_agent}:[/blue bold] {text}")
            elif msg_type == 'task':
                payload = data.get('payload', {})
                console.print(f"\n[yellow bold]📋 新任务:[/yellow bold] {payload.get('title', '')}")
                console.print(f"[dim]    描述: {payload.get('description', '')}[/dim]")
            elif msg_type == 'broadcast':
                from_agent = data.get('from', 'unknown')
                text = data.get('payload', {}).get('text', '')
                console.print(f"\n[magenta bold]📢 广播 from {from_agent}:[/magenta bold] {text}")
            elif msg_type == 'status_change':
                payload = data.get('payload', {})
                console.print(f"\n[dim]🔔 Agent {payload.get('agent_id')} 状态变为 {payload.get('status')}[/dim]")

        client.on('message', on_message)
        client.on('task', on_message)
        client.on('broadcast', on_message)
        client.on('status_change', on_message)

        console.print(f"[bold green]🎧 开始监听消息...[/bold green]")
        console.print(f"[dim]Agent ID: {agent_id}[/dim]")
        console.print("[dim]按 Ctrl+C 停止监听[/dim]\n")

        if await client.connect(ctx.obj['server']):
            try:
                while client.connected:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]停止监听...[/yellow]")
            finally:
                await client.disconnect()
        else:
            console.print(f"[red]✗ 连接服务器失败[/red]")

    run_async(_listen())


@cli.command()
@click.option('--agent', '-a', required=True, help='Agent ID')
@click.option('--task-id', '-t', required=True, help='任务ID')
@click.option('--status', '-s',
              type=click.Choice(['in_progress', 'completed', 'failed', 'cancelled']),
              required=True, help='新状态')
@click.option('--result', '-r', help='结果JSON')
@click.pass_context
def update_task(ctx, agent, task_id, status, result):
    """更新任务状态"""
    async def _update():
        with console.status(f"[bold]更新任务状态..."):
            client = AgentClient(agent, agent)
            if await client.connect(ctx.obj['server']):
                result_data = json.loads(result) if result else None
                success = await client.update_task(task_id, status, result_data)
                if success:
                    console.print(f"[green]✓[/green] 任务 [bold]{task_id}[/bold] 已更新: {status}")
                else:
                    console.print(f"[red]✗[/red] 更新失败")
                await client.disconnect()
            else:
                console.print(f"[red]✗[/red] 连接服务器失败")

    run_async(_update())


@cli.command('interactive')
@click.pass_context
def interactive_mode(ctx):
    """交互模式 - 实时监控和操作"""
    async def _interactive():
        import aiohttp

        console.print(Panel(
            "[bold cyan]Agent Mesh 交互式控制台[/bold cyan]\n\n"
            "输入命令编号或直接输入指令",
            title="欢迎"
        ))

        while True:
            console.print("\n[bold]请选择操作:[/bold]")
            console.print("  [1] 查看状态")
            console.print("  [2] 列出Agent")
            console.print("  [3] 发送消息")
            console.print("  [4] 创建任务")
            console.print("  [5] 广播消息")
            console.print("  [6] 监听消息")
            console.print("  [7] 刷新待确认列表")
            console.print("  [0] 退出")

            choice = Prompt.ask("[bold cyan]>[/bold cyan]", default="0")

            if choice == "0":
                console.print("[yellow]退出交互模式[/yellow]")
                break
            elif choice == "1":
                await show_status()
            elif choice == "2":
                await list_agents()
            elif choice == "3":
                await interactive_send()
            elif choice == "4":
                await interactive_task()
            elif choice == "5":
                await interactive_broadcast()
            elif choice == "6":
                await interactive_listen()
            elif choice == "7":
                await show_pending()
            else:
                console.print("[red]无效选择[/red]")

    async def show_status():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:18801/api/stats") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        console.print(Panel(
                            f"在线: [green]{data.get('online_count', 0)}[/green] | "
                            f"已注册: {data.get('agents', {}).get('confirmed_count', 0)} | "
                            f"待确认: [yellow]{data.get('agents', {}).get('pending_count', 0)}[/yellow] | "
                            f"队列: {data.get('queue_size', 0)}",
                            title="状态"
                        ))
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")

    async def list_agents():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:18801/api/agents") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        agents = data.get('agents', [])
                        if not agents:
                            console.print("[dim]暂无Agent[/dim]")
                            return
                        for i, a in enumerate(agents, 1):
                            status_icon = "🟢" if a.get('status') == 'online' else "🔴"
                            console.print(f"  {i}. {status_icon} {a.get('name')} [{a.get('id')}] - {a.get('type')}")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")

    async def show_pending():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:18801/api/agents/pending") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        agents = data.get('agents', [])
                        if not agents:
                            console.print("[dim]暂无待确认Agent[/dim]")
                            return
                        for a in agents:
                            console.print(f"  ⏳ {a.get('name')} [{a.get('id')}] - {a.get('type')}")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")

    async def interactive_send():
        sender = Prompt.ask("[bold cyan]发送者Agent ID[/bold cyan]")
        target = Prompt.ask("[bold cyan]接收者Agent ID[/bold cyan]")
        message = Prompt.ask("[bold cyan]消息内容[/bold cyan]")
        await send_message_cli(sender, target, message)

    async def interactive_task():
        sender = Prompt.ask("[bold cyan]发送者Agent ID[/bold cyan]")
        target = Prompt.ask("[bold cyan]接收者Agent ID[/bold cyan]")
        title = Prompt.ask("[bold cyan]任务标题[/bold cyan]")
        desc = Prompt.ask("[bold cyan]任务描述[/bold cyan]", default="")
        priority = Prompt.ask("[bold cyan]优先级[/bold cyan]", default="normal")
        await create_task_cli(sender, target, title, desc, priority)

    async def interactive_broadcast():
        sender = Prompt.ask("[bold cyan]发送者Agent ID[/bold cyan]")
        message = Prompt.ask("[bold cyan]广播内容[/bold cyan]")
        target = Prompt.ask("[bold cyan]目标[/bold cyan]", default="*")
        await broadcast_cli(sender, message, target)

    async def interactive_listen():
        agent = Prompt.ask("[bold cyan]Agent ID（留空生成随机ID）[/bold cyan]", default="")
        console.print(f"[green]开始监听... (Ctrl+C停止)[/green]")
        listener = AgentClient(agent or f"inter-{id(asyncio)}", agent or "Interactive")

        def on_msg(data):
            console.print(f"\n[blue]{data.get('type')}: {json.dumps(data.get('payload', {}), ensure_ascii=False)}[/blue]")

        listener.on('message', on_msg)
        listener.on('task', on_msg)
        listener.on('broadcast', on_msg)

        if await listener.connect(ctx.obj['server']):
            try:
                while listener.connected:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                await listener.disconnect()

    async def send_message_cli(from_a, to, msg):
        client = AgentClient(from_a, from_a)
        if await client.connect(ctx.obj['server']):
            success = await client.send_message(to, msg)
            console.print(f"[green]✓ 消息已发送[/green]" if success else "[red]✗ 发送失败[/red]")
            await client.disconnect()

    async def create_task_cli(from_a, to, title, desc, priority):
        client = AgentClient(from_a, from_a)
        if await client.connect(ctx.obj['server']):
            success = await client.create_task(to, title, desc, priority)
            console.print(f"[green]✓ 任务已创建[/green]" if success else "[red]✗ 创建失败[/red]")
            await client.disconnect()

    async def broadcast_cli(from_a, msg, target):
        client = AgentClient(from_a, from_a)
        if await client.connect(ctx.obj['server']):
            success = await client.broadcast(msg, target)
            console.print(f"[green]✓ 广播已发送[/green]" if success else "[red]✗ 发送失败[/red]")
            await client.disconnect()

    run_async(_interactive())


def main():
    """主入口"""
    cli(obj={})


if __name__ == '__main__':
    main()
