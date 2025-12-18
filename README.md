# Acanthopys: Generador de Parsers PEG

Acanthopys es una herramienta profesional para la generación de parsers Packrat (PEG) en Python. Diseñada para ser simple, elegante y potente, permite definir gramáticas complejas, probarlas de forma integrada y generar código Python optimizado y listo para usar.

## Características Principales

*   **Gramáticas PEG**: Soporte completo para Parsing Expression Grammars, eliminando la ambigüedad.
*   **Memoización (Packrat)**: Garantiza un tiempo de ejecución lineal O(n) mediante el cacheo de resultados.
*   **Tests Integrados**: Define casos de prueba directamente en el archivo de gramática para un desarrollo TDD (Test Driven Development) fluido.
*   **Generación de AST**: Creación automática de nodos del Árbol de Sintaxis Abstracta (AST) con una representación limpia y legible.
*   **Múltiples Gramáticas**: Soporte para definir múltiples gramáticas en un solo archivo `.apy`.
*   **CLI Robusta**: Interfaz de línea de comandos con colores, flags y reportes de error detallados.

## Instalación

No requiere instalación compleja. Asegúrate de tener Python 3.8+ instalado.

```bash
git clone https://github.com/Andres95123/Acanthopys.git
cd acanthopys
```

## Uso Básico

### 1. Definir la Gramática (`.apy`)

Crea un archivo con extensión `.apy`. La estructura básica es:

```acantho
grammar NombreGramatica:
    tokens:
        # Definición de tokens (Nombre: Regex)
        # Importante: El orden importa (prioridad de arriba a abajo)
        NUMBER: \d+
        PLUS: \+
        WS: skip \s+  # 'skip' ignora el token (útil para espacios)
    end

    # 'start rule' define el punto de entrada del parser
    start rule StartRule:
        # Reglas de producción
        | left:Term PLUS right:StartRule -> AddNode(left, right)
        | child:Term -> pass  # 'pass' eleva el resultado sin crear nodo
    end

    rule Term:
        | value:NUMBER -> NumberNode(float(value))
    end

    # Test suite para la regla por defecto (StartRule)
    test MisTests:
        "1 + 2" => Yields(AddNode(NumberNode(1.0), NumberNode(2.0)))
        "1 + a" => Fail
    end

    # Test suite especifico para una regla (Term)
    test TermTests Term:
        "42" => Yields(NumberNode(42.0))
    end
end
```

### 2. Generar el Parser

Ejecuta el script principal pasando tu archivo de gramática:

```bash
python acanthopys/main.py mi_gramatica.apy
```

Esto generará un archivo `NombreGramatica_parser.py` en el directorio actual (o el especificado con `-o`).

### 3. Opciones del CLI

*   `input`: Archivo de entrada `.apy`.
*   `-o`, `--output`: Directorio de salida para los archivos generados (default: `.`).
*   `--no-tests`: Desactiva la ejecución de los tests integrados (no recomendado).
*   `--tests`: Ejecuta solo los tests sin generar el archivo parser. Ideal para desarrollo iterativo y CI/CD.

## Sintaxis Detallada

### Tokens
Los tokens se definen con expresiones regulares de Python.
*   `NOMBRE: PATRON`
*   `NOMBRE: skip PATRON` (El token se consume pero no se emite al parser).

**Importante:**
1.  **Orden:** El orden de definición importa. Los tokens se evalúan de arriba a abajo. Define los tokens más específicos antes que los generales.
    *   Ejemplo: `int` (palabra clave) debe ir antes que `[a-zA-Z_]\w*` (identificador general)
    *   Ejemplo: `==` debe ir antes que `=`
    *   Ejemplo: Comentarios deben ir al principio para que `/` no se tome como división
2.  **Espacios:** El generador toma el patrón tal cual (incluyendo espacios). Si usas el operador `|` (OR), asegúrate de no dejar espacios alrededor a menos que quieras que el espacio sea parte del patrón.
    *   Correcto: `COMMENT: //.*|/\*.*\*/`
    *   Incorrecto (si no quieres espacios): `COMMENT: //.* | /\*.*\*/`

### Reglas (Rules)
Las reglas definen la estructura sintáctica.

*   **Start Rule**: Puedes marcar una regla como `start rule Nombre:` para indicar que es el punto de entrada principal del parser.
    *   Si **no se especifica**, se usará la primera regla definida (con un warning recomendando añadir `start`).
    *   Si hay **múltiples** reglas marcadas con `start`, se genera un error.
    *   Ejemplo: `start rule Expression:` marca `Expression` como el punto de entrada.
*   `|` inicia una alternativa.
*   `nombre:Tipo` captura un token o el resultado de otra regla en una variable.
*   `-> Nodo` define qué nodo AST crear.
    *   `-> NombreClase(arg1, arg2)`: Crea una instancia de `NombreClase`.
    *   `-> pass`: Retorna el valor de la variable capturada.
        *   Si hay una sola variable capturada, retorna su valor.
        *   Si no hay variables pero hay un solo término no literal (ej. `| NUMBER -> pass` o `| '(' Expr ')' -> pass`), retorna el token/valor de ese término automáticamente.
        *   Si no hay variables ni términos capturables, retorna `None`.

### Tests
Los bloques `test` permiten verificar la gramática al momento de compilar.

Sintaxis: `test NombreSuite [ReglaObjetivo]:`

*   **ReglaObjetivo (Opcional)**: Si se especifica, los tests se ejecutarán contra esa regla específica en lugar de la regla de inicio. Esto es ideal para probar componentes aislados.
    *   Ejemplo: `test operandTests Operand:` → prueba solo la regla `Operand`.
    *   Si no se especifica, se usa la regla de inicio (marcada con `start` o la primera).

Tipos de aserciones:
*   `"input" => Success`: Espera que el parsing sea exitoso.
*   `"input" => Fail`: Espera que el parsing falle (útil para probar errores de sintaxis).
*   `"input" => Yields(Estructura)`: Espera que el AST resultante coincida exactamente con la estructura dada.
    *   Ejemplo: `'x : int' => Yields(DeclarationNode('x', 'int'))`
    *   **Wildcard `...`**: Puedes usar `...` dentro de un constructor para ignorar los argumentos internos:
        *   `'2 + 8' => Yields(AdditionNode(...))` → Verifica que el resultado sea un `AdditionNode` sin importar sus argumentos.
        *   `'(1 + 2) * 3' => Yields(MultiplicationNode(AdditionNode(...), ...))` → Verifica la estructura pero ignora detalles internos.
        *   Útil para tests de integración donde solo importa el tipo de nodo, no los valores exactos.

**Importante sobre Yields:**
1.  **Sintaxis Obligatoria:** Debes escribir `Yields(...)` - no puedes poner directamente el nodo.
    *   ✅ Correcto: `"1 + 2" => Yields(AddNode(1, 2))`
    *   ❌ Incorrecto: `"1 + 2" => AddNode(1, 2)`
2.  **Representación de Tokens:** Los tokens se representan como strings con comillas simples.
    *   Ejemplo: Si tu regla captura un `identifier`, el test debe usar `'nombre'` no `"nombre"`
    *   Ejemplo: `Variable('int', 'x')` para un token `int` y un identificador `x`
3.  **Comparación Estricta:** La comparación es exacta, caracter por caracter (a menos que uses `...`).

**Errores Comunes:**
*   Olvidar `Yields(...)` → El sistema detectará y reportará un error de sintaxis
*   Usar comillas dobles en lugar de simples para tokens → El test fallará mostrando la diferencia
*   Errores de paréntesis → El sistema detectará paréntesis no balanceados

## Ejemplos

### Calculadora Simple

```acantho
grammar Calc:
    tokens:
        NUM: \d+
        PLUS: \+
        WS: skip \s+
    end

    start rule Expr:
        | l:NUM PLUS r:Expr -> Add(l, r)
        | n:NUM -> Num(int(n))
    end
    
    test CalcTests:
        "1 + 2" => Yields(Add(Num(1), Num(2)))
        "5 + 3 + 2" => Yields(Add(...))  # Solo verifica que sea un Add
    end
    
    test NumTests Expr:
        "42" => Yields(Num(42))
    end
end
```

### Uso del Flag `--tests`

Para desarrollo rápido, puedes ejecutar solo los tests sin generar el parser:

```bash
# Ejecutar solo tests
python acanthopys/main.py mi_gramatica.apy --tests

# Generar el parser (con tests automáticos)
python acanthopys/main.py mi_gramatica.apy

# Generar sin ejecutar tests (no recomendado)
python acanthopys/main.py mi_gramatica.apy --no-tests
```

### JSON Parser (Fragmento)

```acantho
grammar JSON:
    tokens:
        STR: "[^"]*"
        ...
    end

    rule Value:
        | s:STR -> StringNode(s)
        | n:NUMBER -> NumberNode(float(n))
        ...
    end
end
```

## Limitaciones Conocidas

*   No soporta recursión izquierda directa (debido a la naturaleza PEG/Packrat).
*   Las expresiones regulares de los tokens deben ser compatibles con el módulo `re` de Python.

## Soporte en VS Code

Para obtener resaltado de sintaxis en archivos `.apy`, copia la carpeta `acantho-lang` a tu directorio de extensiones de VS Code (`~/.vscode/extensions/`).
