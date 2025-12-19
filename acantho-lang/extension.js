const vscode = require('vscode');
const { LanguageClient, TransportKind } = require('vscode-languageclient/node');
const path = require('path');

let client;

function activate(context) {
    // The server is implemented in python
    const serverModule = context.asAbsolutePath(path.join('server.py'));
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';

    // If the extension is launched in debug mode then the debug server options are used
    // Otherwise the run options are used
    const serverOptions = {
        run: { command: pythonCommand, args: [serverModule] },
        debug: { command: pythonCommand, args: [serverModule] }
    };

    // Options to control the language client
    const clientOptions = {
        // Register the server for plain text documents
        documentSelector: [{ scheme: 'file', language: 'acanthophis' }],
        synchronize: {
            // Notify the server about file changes to '.clientrc files contained in the workspace
            fileEvents: vscode.workspace.createFileSystemWatcher('**/.clientrc')
        }
    };

    // Create the language client and start the client.
    client = new LanguageClient(
        'acanthoLanguageServer',
        'Acantho Language Server',
        serverOptions,
        clientOptions
    );

    // Start the client. This will also launch the server
    client.start();

    // Register restart command
    context.subscriptions.push(vscode.commands.registerCommand('acanthophis.restartServer', () => {
        if (client) {
            client.stop().then(() => {
                client.start();
                vscode.window.showInformationMessage('Acantho Language Server restarted.');
            });
        } else {
            client.start();
            vscode.window.showInformationMessage('Acantho Language Server started.');
        }
    }));

    // Register showAST command
    context.subscriptions.push(vscode.commands.registerCommand('acanthophis.showAST', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor found.');
            return;
        }

        const filePath = editor.document.fileName;
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
        const workspacePath = workspaceFolder ? workspaceFolder.uri.fsPath : path.dirname(filePath);

        // Use the executable
        const executablePath = context.asAbsolutePath(path.join('bin', 'acanthophis.exe'));
        const cp = require('child_process');

        const outputChannel = vscode.window.createOutputChannel("Acantho AST");
        outputChannel.show(true);
        outputChannel.appendLine(`Generating AST for ${filePath}...`);

        cp.exec(`"${executablePath}" ast "${filePath}"`, (err, stdout, stderr) => {
            if (err) {
                outputChannel.appendLine(`Error: ${err.message}`);
                if (stderr) outputChannel.appendLine(`Stderr: ${stderr}`);
                return;
            }

            try {
                const astData = JSON.parse(stdout);

                const panel = vscode.window.createWebviewPanel(
                    'acanthoAST',
                    'Acantho AST Visualization',
                    vscode.ViewColumn.Two,
                    {
                        enableScripts: true,
                        retainContextWhenHidden: true
                    }
                );

                panel.webview.html = getWebviewContent(astData);

            } catch (e) {
                outputChannel.appendLine(`Error parsing AST JSON: ${e.message}`);
                outputChannel.appendLine(stdout);
            }
        });
    }));
}

function getWebviewContent(astData) {
    const rules = astData[0].rules;
    const tokens = astData[0].tokens;

    const nodes = [];
    const links = [];
    const ruleNames = new Set(rules.map(r => r.name));

    // Add Rule Nodes
    rules.forEach(rule => {
        nodes.push({
            id: rule.name,
            group: rule.is_start ? "start" : "rule",
            details: rule
        });

        rule.expressions.forEach(expr => {
            expr.terms.forEach(term => {
                if (ruleNames.has(term.object_related)) {
                    links.push({ source: rule.name, target: term.object_related, type: "rule-ref" });
                } else {
                    // It's likely a token or literal
                    // We can add token nodes if we want, or just ignore for high-level view
                    // Let's add token nodes if they exist in tokens list
                    const isToken = tokens.some(t => t.name === term.object_related);
                    if (isToken) {
                        // Optional: Add token nodes to graph? Might get too busy.
                        // Let's stick to rule dependencies for now.
                    }
                }
            });
        });
    });

    const data = { nodes, links };

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acantho AST</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { margin: 0; overflow: hidden; background-color: #1e1e1e; color: #ccc; font-family: sans-serif; }
        #graph { width: 100vw; height: 100vh; }
        .tooltip {
            position: absolute;
            text-align: left;
            padding: 8px;
            font: 12px sans-serif;
            background: #333;
            border: 1px solid #555;
            border-radius: 4px;
            pointer-events: none;
            opacity: 0;
            color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.5);
            max-width: 300px;
        }
    </style>
</head>
<body>
    <div id="graph"></div>
    <div class="tooltip"></div>
    <script>
        const data = ${JSON.stringify(data)};
        
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(d3.zoom().on("zoom", (event) => {
                g.attr("transform", event.transform);
            }));
            
        const g = svg.append("g");
        
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide(50));

        // Arrow marker
        svg.append("defs").selectAll("marker")
            .data(["end"])
            .enter().append("marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");

        const link = g.append("g")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .selectAll("line")
            .data(data.links)
            .join("line")
            .attr("marker-end", "url(#arrow)");

        const node = g.append("g")
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5)
            .selectAll("circle")
            .data(data.nodes)
            .join("circle")
            .attr("r", 10)
            .attr("fill", d => d.group === "start" ? "#4CAF50" : "#2196F3")
            .call(drag(simulation));

        const label = g.append("g")
            .selectAll("text")
            .data(data.nodes)
            .join("text")
            .attr("dx", 15)
            .attr("dy", 4)
            .text(d => d.id)
            .attr("fill", "#ddd")
            .style("font-size", "12px")
            .style("pointer-events", "none");

        const tooltip = d3.select(".tooltip");

        node.on("mouseover", (event, d) => {
            tooltip.transition().duration(200).style("opacity", .9);
            
            let content = "<strong>" + d.id + "</strong><br/>";
            if (d.details.expressions) {
                content += "<ul>";
                d.details.expressions.forEach(expr => {
                    const terms = expr.terms.map(t => t.object_related).join(" ");
                    content += "<li>" + terms + " -> " + (expr.return_object || "pass") + "</li>";
                });
                content += "</ul>";
            }
            
            tooltip.html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", (d) => {
            tooltip.transition().duration(500).style("opacity", 0);
        });

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
                
            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });

        function drag(simulation) {
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
            
            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }
    </script>
</body>
</html>`;
}

function deactivate() {
    if (!client) {
        return undefined;
    }
    return client.stop();
}

module.exports = {
    activate,
    deactivate
};
