# multiagent-system
Sistema multiagente orquestado por n8n, con agentes y MCP, para generar y desplegar proyectos backend.

## Estructura del repositorio

### agents/
Contiene los agentes principales del sistema, cada uno con una responsabilidad clara dentro del flujo multiagente:

- *planner/*  
  Genera planes y tareas que definen qué debe hacerse.

- *developer/*  
  Implementa el código necesario según los planes generados.

- *reviewer/*  
  Revisa el código generado para asegurar calidad y consistencia.

- *deployer/*  
  Gestiona el despliegue del proyecto backend generado.

### common/
Utilidades y módulos compartidos entre los agentes.  
Actualmente vacío, se irá completando conforme evolucione el sistema.

### config/
Archivos de configuración inicial y placeholders.  
No contiene valores reales todavía; se completará en fases posteriores.
