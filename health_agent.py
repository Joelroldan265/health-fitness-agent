import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.google import Gemini
import os
import time
from datetime import datetime
import json

st.set_page_config(
    page_title="AI Health & Fitness Planner",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0fff4;
        border: 1px solid #9ae6b4;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fffaf0;
        border: 1px solid #fbd38d;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Obtener API Key de Streamlit Secrets
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("❌ API Key no configurada en Streamlit Secrets")
    st.info("Por favor, contacta al administrador para configurar la API Key")
    st.stop()

def run_with_retry(agent, user_profile, max_retries=3):
    """Ejecuta una solicitud con reintentos automáticos"""
    for attempt in range(max_retries):
        try:
            result = agent.run(user_profile)
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"⚠️ Intento {attempt + 1} falló. Reintentando en 2 segundos...")
                time.sleep(2)
            else:
                raise e

def generate_pdf_content(user_profile_dict, dietary_plan, fitness_plan):
    """Genera contenido para descargar"""
    content = f"""
╔════════════════════════════════════════════════════════════════╗
║        PLAN PERSONALIZADO DE SALUD Y FITNESS CON IA            ║
║                   Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}                    ║
╚════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════
📋 TU PERFIL
═══════════════════════════════════════════════════════════════════

Edad: {user_profile_dict['age']} años
Peso: {user_profile_dict['weight']} kg
Altura: {user_profile_dict['height']} cm
Sexo: {user_profile_dict['sex']}
Nivel de Actividad: {user_profile_dict['activity_level']}
Preferencias Dietéticas: {user_profile_dict['dietary_preferences']}
Objetivos de Fitness: {user_profile_dict['fitness_goals']}

══════════════════���════════════════════════════════════════════════
🍽️ PLAN DIETÉTICO PERSONALIZADO - 7 DÍAS
═══════════════════════════════════════════════════════════════════

🎯 Por qué funciona este plan:
{dietary_plan.get('why_this_plan_works', 'Información no disponible')}

📊 Plan de Comidas por Semana:
{dietary_plan.get('meal_plan', 'Plan no disponible')}

📚 Guía de Alimentos para Combinar:
{dietary_plan.get('food_guide', 'Guía no disponible')}

⚠️ Consideraciones Importantes:
{dietary_plan.get('important_considerations', 'Información no disponible')}

═══════════════════════════════════════════════════════════════════
💪 PLAN DE FITNESS PERSONALIZADO - 7 DÍAS
═══════════════════════════════════════════════════════════════════

🎯 Objetivos:
{fitness_plan.get('goals', 'Objetivos no especificados')}

🏋️‍♂️ Rutina de Ejercicios por Semana:
{fitness_plan.get('routine', 'Rutina no disponible')}

💡 Consejos Pro:
{fitness_plan.get('tips', 'Consejos no disponibles')}

═══════════════════════════════════════════════════════════════════
✨ Recuerda:
- Variabilidad: Cambia tus comidas durante la semana
- Hidratación: Bebe mucha agua diariamente
- Descanso: Duerme 7-8 horas cada noche
- Consistencia: Sé constante con tu plan
- Flexibilidad: Ajusta según cómo se sienta tu cuerpo
═══════════════════════════════════════════════════════════════════
"""
    return content

def display_dietary_plan(plan_content):
    with st.expander("📋 Tu Plan Dietético Personalizado - 7 Días", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Por qué funciona este plan")
            st.info(plan_content.get("why_this_plan_works", "Información no disponible"))
            
            st.markdown("### 🍽️ Plan de Comidas por Semana (Variado)")
            st.write(plan_content.get("meal_plan", "Plan no disponible"))
            
            st.markdown("### 📚 Guía de Alimentos para Combinar")
            st.write(plan_content.get("food_guide", "Guía no disponible"))
        
        with col2:
            st.markdown("### ⚠️ Consideraciones Importantes")
            considerations = plan_content.get("important_considerations", "").split('\n')
            for consideration in considerations:
                if consideration.strip():
                    st.warning(consideration)

def display_fitness_plan(plan_content):
    with st.expander("💪 Tu Plan de Fitness Personalizado - 7 Días", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Objetivos")
            st.success(plan_content.get("goals", "Objetivos no especificados"))
            
            st.markdown("### 🏋️‍♂️ Rutina de Ejercicios por Semana")
            st.write(plan_content.get("routine", "Rutina no disponible"))
        
        with col2:
            st.markdown("### 💡 Consejos Pro")
            tips = plan_content.get("tips", "").split('\n')
            for tip in tips:
                if tip.strip():
                    st.info(tip)

def main():
    if 'dietary_plan' not in st.session_state:
        st.session_state.dietary_plan = {}
        st.session_state.fitness_plan = {}
        st.session_state.qa_pairs = []
        st.session_state.plans_generated = False
        st.session_state.user_profile = {}

    st.title("🏋️‍♂️ Planificador de Salud y Fitness con IA")
    st.markdown("""
        <div style='background-color: #4CAF50; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem; color: white;'>
        Obtén planes personalizados de dieta y fitness adaptados a tus objetivos y preferencias.
        Nuestro sistema impulsado por IA considera tu perfil único para crear el plan perfecto para ti.
        </div>
    """, unsafe_allow_html=True)

    st.header("👤 Tu Perfil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Edad", min_value=10, max_value=100, step=1, help="Ingresa tu edad")
        height = st.number_input("Altura (cm)", min_value=100.0, max_value=250.0, step=0.1)
        activity_level = st.selectbox(
            "Nivel de Actividad",
            options=["Sedentario", "Ligero", "Moderado", "Muy Activo", "Extremadamente Activo"],
            help="Elige tu nivel de actividad típico"
        )
        dietary_preferences = st.selectbox(
            "Preferencias Dietéticas",
            options=["Vegetariano", "Keto", "Sin Gluten", "Bajo en Carbohidratos", "Sin Lácteos"],
            help="Selecciona tu preferencia dietética"
        )

    with col2:
        weight = st.number_input("Peso (kg)", min_value=20.0, max_value=300.0, step=0.1)
        sex = st.selectbox("Sexo", options=["Masculino", "Femenino", "Otro"])
        fitness_goals = st.selectbox(
            "Objetivos de Fitness",
            options=["Perder Peso", "Ganar Músculo", "Resistencia", "Mantenerse en Forma", "Entrenamiento de Fuerza"],
            help="¿Qué quieres lograr?"
        )

    if st.button("🎯 Generar Mi Plan Personalizado - 7 Días", use_container_width=True):
        with st.spinner("Creando tu rutina perfecta de salud y fitness para toda la semana... (Esto puede tomar 1-2 minutos)"):
            try:
                gemini_model = Gemini(id="gemini-2.5-flash", api_key=gemini_api_key)
                
                dietary_agent = Agent(
                    name="Experto en Nutrición",
                    role="Proporciona recomendaciones dietéticas personalizadas",
                    model=gemini_model,
                    instructions=[
                        "Considera la entrada del usuario, incluyendo restricciones y preferencias dietéticas.",
                        "IMPORTANTE: Sugiere un plan de comidas VARIADO para TODA UNA SEMANA (Lunes a Domingo).",
                        "Cada día debe tener desayuno, almuerzo, cena y meriendas DIFERENTES.",
                        "Incluye una guía de combinaciones de alimentos que el usuario puede usar para crear sus propias comidas.",
                        "La guía debe mostrar qué proteínas, carbohidratos y grasas saludables puede combinar.",
                        "Proporciona una breve explicación de por qué el plan es adecuado para los objetivos del usuario.",
                        "Enfócate en variedad, claridad, coherencia y calidad de las recomendaciones.",
                        "IMPORTANTE: Responde SIEMPRE en español.",
                    ]
                )

                fitness_agent = Agent(
                    name="Experto en Fitness",
                    role="Proporciona recomendaciones de fitness personalizadas",
                    model=gemini_model,
                    instructions=[
                        "Proporciona ejercicios personalizados según los objetivos del usuario.",
                        "IMPORTANTE: Crea un plan de entrenamiento VARIADO para TODA UNA SEMANA (Lunes a Domingo).",
                        "Cada día debe tener ejercicios DIFERENTES, alternando grupos musculares.",
                        "Incluye días de descanso o ejercicio ligero cuando sea apropiado.",
                        "Para cada día, incluye calentamiento, ejercicios principales y enfriamiento.",
                        "Explica los beneficios de cada ejercicio recomendado.",
                        "Asegúrate de que el plan sea variado, accionable y detallado.",
                        "IMPORTANTE: Responde SIEMPRE en español.",
                    ]
                )

                user_profile = f"""
                Edad: {age}
                Peso: {weight}kg
                Altura: {height}cm
                Sexo: {sex}
                Nivel de Actividad: {activity_level}
                Preferencias Dietéticas: {dietary_preferences}
                Objetivos de Fitness: {fitness_goals}
                
                Por favor, proporciona un plan VARIADO para TODA UNA SEMANA (7 días).
                """

                # Ejecutar con reintentos
                dietary_plan_response: RunOutput = run_with_retry(dietary_agent, user_profile)
                dietary_plan = {
                    "why_this_plan_works": "Plan variado de 7 días - Proteína Alta, Grasas Saludables, Carbohidratos Moderados y Balance Calórico",
                    "meal_plan": dietary_plan_response.content,
                    "food_guide": "Guía incluida en el plan de comidas anterior",
                    "important_considerations": """
                    - Variabilidad: Come diferente cada día para no aburrirte
                    - Hidratación: Bebe al menos 2-3 litros de agua diarios
                    - Electrolitos: Monitorea sodio, potasio y magnesio
                    - Fibra: Asegúrate de una ingesta adecuada a través de verduras y frutas
                    - Flexibilidad: Puedes cambiar el orden de los días según tu conveniencia
                    - Escucha tu cuerpo: Ajusta los tamaños de las porciones según sea necesario
                    """
                }

                fitness_plan_response: RunOutput = run_with_retry(fitness_agent, user_profile)
                fitness_plan = {
                    "goals": "Plan variado de 7 días - Construir fuerza, mejorar resistencia y mantener la forma física general",
                    "routine": fitness_plan_response.content,
                    "tips": """
                    - Registra tu progreso regularmente
                    - Permite un descanso adecuado entre entrenamientos (48 horas para el mismo grupo muscular)
                    - Enfócate en la forma correcta antes de aumentar el peso
                    - Mantén consistencia con tu rutina
                    - La variedad es la clave - cambia ejercicios cada 4-6 semanas
                    - Aumenta gradualmente la intensidad
                    """
                }

                # Guardar en sesión
                st.session_state.dietary_plan = dietary_plan
                st.session_state.fitness_plan = fitness_plan
                st.session_state.plans_generated = True
                st.session_state.qa_pairs = []
                st.session_state.user_profile = {
                    "age": age,
                    "weight": weight,
                    "height": height,
                    "sex": sex,
                    "activity_level": activity_level,
                    "dietary_preferences": dietary_preferences,
                    "fitness_goals": fitness_goals
                }

                st.success("✅ ¡Planes de 7 días generados exitosamente!")
                display_dietary_plan(dietary_plan)
                display_fitness_plan(fitness_plan)

            except Exception as e:
                st.error(f"❌ Ocurrió un error después de múltiples intentos: {e}")
                st.info("💡 Consejo: Por favor, intenta de nuevo en unos momentos. La API podría estar temporalmente ocupada.")

    # Mostrar opciones de descarga si hay planes generados
    if st.session_state.plans_generated:
        st.markdown("---")
        st.subheader("📥 Descargar Tu Plan de 7 Días")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar como TXT
            txt_content = generate_pdf_content(
                st.session_state.user_profile,
                st.session_state.dietary_plan,
                st.session_state.fitness_plan
            )
            st.download_button(
                label="📄 Descargar como TXT",
                data=txt_content,
                file_name=f"Plan_Salud_Fitness_7Dias_{datetime.now().strftime('%d_%m_%Y')}.txt",
                mime="text/plain"
            )
        
        with col2:
            # Descargar como JSON
            json_data = {
                "fecha_generacion": datetime.now().isoformat(),
                "duracion_plan": "7 días",
                "perfil_usuario": st.session_state.user_profile,
                "plan_dietetico": st.session_state.dietary_plan,
                "plan_fitness": st.session_state.fitness_plan
            }
            json_content = json.dumps(json_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📊 Descargar como JSON",
                data=json_content,
                file_name=f"Plan_Salud_Fitness_7Dias_{datetime.now().strftime('%d_%m_%Y')}.json",
                mime="application/json"
            )

    if st.session_state.plans_generated:
        st.header("❓ ¿Preguntas sobre tu plan?")
        question_input = st.text_input("¿Qué te gustaría saber?")

        if st.button("Obtener Respuesta"):
            if question_input:
                with st.spinner("Encontrando la mejor respuesta para ti..."):
                    dietary_plan = st.session_state.dietary_plan
                    fitness_plan = st.session_state.fitness_plan

                    context = f"Plan Dietético: {dietary_plan.get('meal_plan', '')}\n\nPlan de Fitness: {fitness_plan.get('routine', '')}"
                    full_context = f"{context}\nPregunta del Usuario: {question_input}\n\nIMPORTANTE: Responde SIEMPRE en español."

                    try:
                        gemini_model = Gemini(id="gemini-2.5-flash", api_key=gemini_api_key)
                        agent = Agent(
                            model=gemini_model, 
                            debug_mode=True, 
                            markdown=True,
                            instructions=["Responde siempre en español de manera clara y útil."]
                        )
                        run_response: RunOutput = run_with_retry(agent, full_context)

                        if hasattr(run_response, 'content'):
                            answer = run_response.content
                        else:
                            answer = "Lo siento, no pude generar una respuesta en este momento."

                        st.session_state.qa_pairs.append((question_input, answer))
                        st.success("✅ ¡Respuesta generada!")
                    except Exception as e:
                        st.error(f"❌ Ocurrió un error al obtener la respuesta: {e}")

        if st.session_state.qa_pairs:
            st.header("💬 Historial de Preguntas y Respuestas")
            for question, answer in st.session_state.qa_pairs:
                st.markdown(f"**P:** {question}")
                st.markdown(f"**R:** {answer}")

if __name__ == "__main__":
    main()
