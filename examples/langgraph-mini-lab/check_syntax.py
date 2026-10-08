"""只检查语法和可静态识别的图结构，不会导入或运行 LangGraph。"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def literal_nodes(expr):
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return [expr.value]
    if isinstance(expr, ast.Name) and expr.id in {"START", "END"}:
        return [expr.id]
    if isinstance(expr, (ast.List, ast.Tuple)):
        return [name for element in expr.elts for name in literal_nodes(element)]
    if isinstance(expr, ast.Dict):
        return [name for element in expr.values for name in literal_nodes(element)]
    return []


def check_graph(path: Path, expected_count: int | None) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path),
                     feature_version=(3, 11))
    class_keys = {"MessagesState": {"messages"}}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            keys = {item.target.id for item in node.body
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)}
            for base in node.bases:
                if isinstance(base, ast.Name):
                    keys |= class_keys.get(base.id, set())
            class_keys[node.name] = keys
    builders = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id == "StateGraph"):
            schema = node.value.args[0]
            for target in node.targets:
                if isinstance(target, ast.Name):
                    builders[target.id] = {"keys": class_keys.get(getattr(schema, "id", ""), set()),
                                           "nodes": [], "edges": []}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)):
            continue
        builder = builders.get(node.func.value.id)
        if builder is None:
            continue
        if node.func.attr == "add_node":
            builder["nodes"] += literal_nodes(node.args[0])
        elif node.func.attr == "add_edge":
            builder["edges"] += literal_nodes(node.args[0]) + literal_nodes(node.args[1])
        elif node.func.attr == "add_conditional_edges":
            builder["edges"] += literal_nodes(node.args[0])
            if len(node.args) >= 3:
                builder["edges"] += literal_nodes(node.args[2])
    for name, builder in builders.items():
        nodes = builder["nodes"]
        if len(nodes) != len(set(nodes)):
            raise ValueError(f"{path.name}: {name} 存在重复节点名")
        conflicts = set(nodes) & builder["keys"]
        if conflicts:
            raise ValueError(f"{path.name}: 节点名和状态字段冲突: {conflicts}")
        unknown = set(builder["edges"]) - set(nodes) - {"START", "END"}
        if unknown:
            raise ValueError(f"{path.name}: 连线引用未注册节点: {unknown}")
    if expected_count is not None and len(builders["builder"]["nodes"]) != expected_count:
        raise ValueError(f"{path.name}: 顶层节点数不符合清单")


def main() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    counts = {item["path"]: item["nodes"] for item in manifest}
    counts["optional/22_real_tool_agent.py"] = 3
    files = [path for path in ROOT.rglob("*.py")
             if not any(part in {".venv", "__pycache__", ".runtime"} for part in path.parts)]
    for path in sorted(files):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        check_graph(path, counts.get(path.relative_to(ROOT).as_posix()))
    print(f"PASS: {len(files)} 个 Python 文件语法检查通过。")
    print(f"PASS: {len(counts)} 个示例的顶层节点数、节点/字段命名、静态连线检查通过。")
    print("注意：以上不是 LangGraph 运行测试；安装依赖后请运行 run_all.py。")


if __name__ == "__main__":
    main()
