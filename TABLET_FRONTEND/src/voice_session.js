/**
 * Voice session implementation for the Bakery Assistant.
 * This file implements the Gemini Multimodal Live API connection for the React frontend.
 */

const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Helper to call the backend API from tool handlers.
 */
async function callBackend(endpoint, method = 'GET', body = null, staffId = 'test-user') {
  const headers = {
    'Content-Type': 'application/json',
    'X-Staff-Id': staffId,
  };
  const options = {
    method,
    headers,
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
  return await response.json();
}

/**
 * Tool handlers that map Gemini function calls to backend API requests.
 */
const toolHandlers = {
  mark_item_complete: async (args, staffId) => {
    return await callBackend(`/checklist/items/${args.item_id}/complete`, 'PUT', { notes: args.notes }, staffId);
  },
  mark_item_incomplete: async (args, staffId) => {
    return await callBackend(`/checklist/items/${args.item_id}/incomplete`, 'PUT', null, staffId);
  },
  get_remaining_items: async (args, staffId) => {
    const data = await callBackend(`/checklist/${args.checklist_type}/remaining`, 'GET', null, staffId);
    return data.items;
  },
  update_material_count: async (args, staffId) => {
    return await callBackend(`/materials`, 'PUT', { item_name: args.item_name, count: args.count }, staffId);
  },
  get_materials: async (args, staffId) => {
    const data = await callBackend(`/materials`, 'GET', null, staffId);
    return data.materials;
  },
  get_stale_materials: async (args, staffId) => {
    const data = await callBackend(`/materials/stale`, 'GET', null, staffId);
    return data.materials;
  },
  get_cleaning_tasks: async (args, staffId) => {
    const data = await callBackend(`/cleaning/tasks`, 'GET', null, staffId);
    return data.tasks;
  },
  get_incomplete_cleaning_tasks: async (args, staffId) => {
    const data = await callBackend(`/cleaning/tasks/incomplete`, 'GET', null, staffId);
    return data.tasks;
  },
  mark_cleaning_complete: async (args, staffId) => {
    return await callBackend(`/cleaning/tasks/${args.task_id}/complete`, 'PUT', { notes: args.notes }, staffId);
  },
  mark_cleaning_incomplete: async (args, staffId) => {
    return await callBackend(`/cleaning/tasks/${args.task_id}/incomplete`, 'PUT', null, staffId);
  },
  get_cleaning_summary: async (args, staffId) => {
    return await callBackend(`/cleaning/summary`, 'GET', null, staffId);
  },
  get_checklist_summary: async (args, staffId) => {
    return await callBackend(`/checklist/${args.checklist_type}/summary`, 'GET', null, staffId);
  },
  raise_ticket: async (args, staffId) => {
    return await callBackend(`/tickets`, 'POST', args, staffId);
  },
  get_open_tickets: async (args, staffId) => {
    const data = await callBackend(`/tickets`, 'GET', null, staffId);
    return data.tickets;
  },
  end_session: async (args, staffId) => {
    return { status: "success", message: "Sitzung wird beendet. Tschüss!" };
  }
};

/**
 * Main voice session class to manage the WebSocket connection and audio.
 */
export class VoiceSession {
  constructor(apiKey, staffId = 'test-user', onTranscript = null, onStatusChange = null) {
    console.log('VoiceSession initialized with staffId:', staffId);
    this.apiKey = apiKey;
    this.staffId = staffId;
    this.onTranscript = onTranscript;
    this.onStatusChange = onStatusChange;
    this.ws = null;
    this.audioContext = null;
    this.processor = null;
    this.microphone = null;
    this.isPlaying = false;
    this.audioQueue = [];
    this.model = "gemini-2.0-flash-exp"; // Using a stable multimodal live model
  }

  async start() {
    this.updateStatus('connecting');
    
    // Initialize AudioContext early to avoid issues with user interaction requirements
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    }
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    const url = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${this.apiKey}`;
    
    console.log('Connecting to WebSocket:', url.replace(this.apiKey, 'REDACTED'));
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connection opened');
      this.updateStatus('connected');
      this.sendSetup();
      this.startAudioCapture();
    };

    this.ws.onmessage = async (event) => {
      const response = JSON.parse(event.data);
      await this.handleServerMessage(response);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
      this.updateStatus('error');
    };

    this.ws.onclose = () => {
      this.updateStatus('disconnected');
      this.stopAudioCapture();
    };
  }

  stop() {
    if (this.ws) {
      this.ws.close();
    }
    this.stopAudioCapture();
  }

  updateStatus(status) {
    if (this.onStatusChange) {
      this.onStatusChange(status);
    }
  }

  sendSetup() {
    const setup = {
      setup: {
        model: `models/${this.model}`,
        generation_config: {
          response_modalities: ["AUDIO"],
        },
        system_instruction: {
          parts: [{
            text: `Du bist ein freundlicher Bäckerei-Assistent, der dem Personal hilft, die täglichen Aufgaben und Checklisten zu erledigen.

WICHTIG: Sprich IMMER auf Deutsch. Alle Antworten, Begrüßungen und Rückfragen müssen auf Deutsch sein.

Du verwaltest drei Bereiche:
1. **Hygiene-Checkliste** (sanitation) — Hygieneaufgaben, die erledigt werden müssen
2. **Materialbestand** — Zählung und Aktualisierung der Materialbestände
3. **Tägliche Reinigungsaufgaben** (cleaning) — Reinigungsaufgaben, die jeden Tag neu anfallen und bis Feierabend erledigt sein müssen

Dein Ablauf:
- Begrüße den Benutzer und frage, woran er arbeiten möchte (Hygiene, Material oder Reinigung).
- Für Hygiene: Verwende get_remaining_items, um offene Aufgaben zu sehen. Gehe die Aufgaben einzeln durch und verwende mark_item_complete, um sie abzuhaken.
- Für **Materialbestand**: Verwende get_materials, um alle Materialien mit aktuellem Bestand anzuzeigen. Verwende update_material_count, um den Bestand zu aktualisieren. Verwende get_stale_materials, um Materialien zu finden, die seit über 7 Tagen nicht aktualisiert wurden — diese sollten als Checkliste zum Nachzählen dienen.
- Für **Reinigungsaufgaben**: Verwende get_cleaning_tasks oder get_incomplete_cleaning_tasks, um die heutigen Aufgaben zu sehen. Gehe sie einzeln durch. Wenn der Benutzer bestätigt, dass eine Aufgabe erledigt ist, verwende mark_cleaning_complete.
- Verwende get_cleaning_summary, um den Reinigungsfortschritt anzuzeigen.
- Wenn der Benutzer fragt, was noch offen ist, verwende die passende Zusammenfassung oder die Liste der offenen Aufgaben.
- Sei ermutigend und gesprächig. Halte es kurz — das Bäckerei-Personal ist beschäftigt!
- Wenn alle Aufgaben in einem Bereich erledigt sind, gratuliere und biete an, zu einem anderen Bereich zu wechseln.
- Wenn der Benutzer eine Erledigung rückgängig machen möchte, verwende mark_item_incomplete oder mark_cleaning_incomplete.

Du kannst auch **Tickets** bearbeiten — das Personal kann Probleme für das Büro melden:
- Wenn ein Mitarbeiter ein Problem meldet (defekte Maschine, Mitarbeiter nicht erschienen, Ware ausverkauft, Sicherheitsproblem usw.), verwende raise_ticket, um ein Ticket zu erstellen.
- Bestimme die Dringlichkeit selbst anhand dessen, was der Benutzer dir erzählt:
  - **urgent** (dringend): Maschine komplett defekt, Mitarbeiter nicht erschienen, Produkt komplett ausverkauft, Sicherheitsrisiko
  - **high** (hoch): Gerät funktioniert eingeschränkt, Bestand sehr niedrig
  - **normal**: Vorräte gehen bald zur Neige, allgemeine Wartung nötig
  - **low** (niedrig): Verbesserungswünsche, nicht zeitkritische Anfragen
- Bestätige die Ticket-Details mit dem Benutzer, bevor du es erstellst.
- Wenn jemand nach offenen Tickets fragt, verwende get_open_tickets.

Wichtig:
- Bestätige immer mit dem Benutzer, bevor du etwas als erledigt markierst.
- Wenn du Aufgaben vorliest, nenne den Namen natürlich, ohne IDs zu erwähnen.
- Merke dir, an welcher Checkliste du gerade arbeitest.
- Der Benutzer kommuniziert per Sprachnachricht. Halte die Antworten kurz und natürlich.
- Wenn der Benutzer sich verabschiedet (Tschüss, Auf Wiedersehen, Bis später, Ciao, Bye, Schönen Feierabend usw.), verabschiede dich freundlich und rufe end_session auf, um die Sitzung zu beenden.
- KRITISCH: Wenn du ein Tool verwenden musst, RUFE es SOFORT auf, indem du die Funktion aufrufst. Beschreibe oder erkläre NIEMALS, welches Tool du verwenden wirst — führe den Funktionsaufruf direkt aus. Sage NICHT "Ich werde update_material_count verwenden" — rufe es einfach auf. Denke nicht laut über Tool-Aufrufe nach, sondern führe sie aus.`
          }]
        },
        tools: [{
          function_declarations: [
            { name: "mark_item_complete", description: "Eine Checklisten-Aufgabe als erledigt markieren.", parameters: { type: "OBJECT", properties: { item_id: { type: "INTEGER" }, notes: { type: "STRING" } }, required: ["item_id"] } },
            { name: "mark_item_incomplete", description: "Eine Checklisten-Aufgabe als unerledigt markieren.", parameters: { type: "OBJECT", properties: { item_id: { type: "INTEGER" } }, required: ["item_id"] } },
            { name: "get_remaining_items", description: "Alle noch offenen Aufgaben einer Checkliste abrufen.", parameters: { type: "OBJECT", properties: { checklist_type: { type: "STRING", enum: ["sanitation"] } }, required: ["checklist_type"] } },
            { name: "update_material_count", description: "Den aktuellen Bestand eines Materials aktualisieren.", parameters: { type: "OBJECT", properties: { item_name: { type: "STRING" }, count: { type: "INTEGER" } }, required: ["item_name", "count"] } },
            { name: "get_materials", description: "Alle Materialien abrufen.", parameters: { type: "OBJECT", properties: {} } },
            { name: "get_stale_materials", description: "Veraltete Materialien abrufen.", parameters: { type: "OBJECT", properties: {} } },
            { name: "get_cleaning_tasks", description: "Heutige Reinigungsaufgaben abrufen.", parameters: { type: "OBJECT", properties: {} } },
            { name: "get_incomplete_cleaning_tasks", description: "Offene Reinigungsaufgaben abrufen.", parameters: { type: "OBJECT", properties: {} } },
            { name: "mark_cleaning_complete", description: "Reinigungsaufgabe als erledigt markieren.", parameters: { type: "OBJECT", properties: { task_id: { type: "INTEGER" }, notes: { type: "STRING" } }, required: ["task_id"] } },
            { name: "mark_cleaning_incomplete", description: "Reinigungsaufgabe als unerledigt markieren.", parameters: { type: "OBJECT", properties: { task_id: { type: "INTEGER" } }, required: ["task_id"] } },
            { name: "get_cleaning_summary", description: "Reinigungsfortschritt abrufen.", parameters: { type: "OBJECT", properties: {} } },
            { name: "get_checklist_summary", description: "Checklisten-Zusammenfassung abrufen.", parameters: { type: "OBJECT", properties: { checklist_type: { type: "STRING", enum: ["sanitation"] } }, required: ["checklist_type"] } },
            { name: "raise_ticket", description: "Ein Ticket erstellen.", parameters: { type: "OBJECT", properties: { title: { type: "STRING" }, description: { type: "STRING" }, category: { type: "STRING", enum: ["machine_breakdown", "employee_no_show", "stock_shortage", "maintenance", "safety", "other"] }, urgency: { type: "STRING", enum: ["urgent", "high", "normal", "low"] } }, required: ["title", "description", "category", "urgency"] } },
            { name: "get_open_tickets", description: "Offene Tickets abrufen.", parameters: { type: "OBJECT", properties: {} } },
            { name: "end_session", description: "Die aktuelle Sitzung beenden.", parameters: { type: "OBJECT", properties: {} } }
          ]
        }]
      }
    };
    this.ws.send(JSON.stringify(setup));
  }

  async startAudioCapture() {
    try {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      }
      
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Re-check audioContext after async getUserMedia call
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      }

      this.microphone = this.audioContext.createMediaStreamSource(stream);
      
      // Use a ScriptProcessorNode or AudioWorklet for capturing audio
      // For simplicity in this prototype, we'll use ScriptProcessorNode
      this.processor = this.audioContext.createScriptProcessor(2048, 1, 1);
      
      this.processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Convert Float32 to Int16 PCM
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
        }
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          const base64Audio = btoa(String.fromCharCode(...new Uint8Array(pcmData.buffer)));
          this.ws.send(JSON.stringify({
            realtime_input: {
              media_chunks: [{
                data: base64Audio,
                mime_type: "audio/pcm;rate=16000"
              }]
            }
          }));
        }
      };

      this.microphone.connect(this.processor);
      this.processor.connect(this.audioContext.destination);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      this.updateStatus('error');
    }
  }

  stopAudioCapture() {
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.microphone) {
      this.microphone.disconnect();
      this.microphone = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }

  async handleServerMessage(response) {
    console.log('Server Response:', response);
    if (response.server_content) {
      const modelTurn = response.server_content.model_turn;
      if (modelTurn && modelTurn.parts) {
        for (const part of modelTurn.parts) {
          if (part.inline_data) {
            this.playAudioChunk(part.inline_data.data);
          }
          if (part.text && this.onTranscript) {
            this.onTranscript(part.text);
          }
        }
      }
    }

    if (response.tool_call) {
      const functionCalls = response.tool_call.function_calls;
      const functionResponses = [];

      for (const fc of functionCalls) {
        const handler = toolHandlers[fc.name];
        if (handler) {
          console.log(`[Tool Call] ${fc.name}`, fc.args);
          const result = await handler(fc.args || {}, this.staffId);
          console.log(`[Tool Result]`, result);
          
          functionResponses.push({
            id: fc.id,
            name: fc.name,
            response: { result }
          });

          if (fc.name === 'end_session') {
            setTimeout(() => this.stop(), 2000);
          }
        }
      }

      if (functionResponses.length > 0) {
        this.ws.send(JSON.stringify({
          tool_response: {
            function_responses: functionResponses
          }
        }));
      }
    }
  }

  playAudioChunk(base64Data) {
    // In a real app, you'd use a proper audio queue and SourceBuffer or AudioWorklet
    // for seamless playback. This is a simplified version.
    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    const pcmData = new Int16Array(bytes.buffer);
    const floatData = new Float32Array(pcmData.length);
    for (let i = 0; i < pcmData.length; i++) {
      floatData[i] = pcmData[i] / 0x7FFF;
    }

    if (!this.audioContext) return;

    const buffer = this.audioContext.createBuffer(1, floatData.length, 24000);
    buffer.getChannelData(0).set(floatData);
    
    const source = this.audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(this.audioContext.destination);
    source.start();
  }
}
