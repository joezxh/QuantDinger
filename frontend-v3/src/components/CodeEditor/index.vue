<template>
  <div ref="editorContainer" class="code-editor-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { EditorState } from '@codemirror/state'
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, dropCursor, rectangularSelection, crosshairCursor, highlightActiveLine } from '@codemirror/view'
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands'
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search'
import { closeBrackets, autocompletion, closeBracketsKeymap, completionKeymap } from '@codemirror/autocomplete'
import { foldGutter, indentOnInput, syntaxHighlighting, defaultHighlightStyle, bracketMatching, foldKeymap } from '@codemirror/language'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'

const { t } = useI18n()
const props = defineProps<{
  modelValue: string
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorContainer = ref<HTMLElement | null>(null)
let view: EditorView | null = null

const basicSetup = [
  lineNumbers(),
  highlightActiveLineGutter(),
  highlightSpecialChars(),
  history(),
  foldGutter(),
  drawSelection(),
  dropCursor(),
  EditorState.allowMultipleSelections.of(true),
  indentOnInput(),
  syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
  bracketMatching(),
  closeBrackets(),
  autocompletion(),
  rectangularSelection(),
  crosshairCursor(),
  highlightActiveLine(),
  highlightSelectionMatches(),
  keymap.of([
    ...closeBracketsKeymap,
    ...defaultKeymap,
    ...searchKeymap,
    ...historyKeymap,
    ...foldKeymap,
    ...completionKeymap
  ])
]

onMounted(() => {
  if (!editorContainer.value) return

  const startState = EditorState.create({
    doc: props.modelValue,
    extensions: [
      basicSetup,
      python(),
      oneDark,
      EditorState.readOnly.of(props.readonly || false),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          emit('update:modelValue', update.state.doc.toString())
        }
      })
    ]
  })

  view = new EditorView({
    state: startState,
    parent: editorContainer.value
  })
})

watch(() => props.modelValue, (newValue) => {
  if (view && newValue !== view.state.doc.toString()) {
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: newValue }
    })
  }
})

watch(() => props.readonly, (newReadonly) => {
  if (view) {
    view.dispatch({
      effects: EditorState.transactionFilter.of(() => {
        return []
      })
    })
    // Note: Re-creating state or managing readonly dynamically is simpler by just reconfiguring.
    // For now we don't fully support toggling readonly dynamically without full re-init.
  }
})

onBeforeUnmount(() => {
  if (view) {
    view.destroy()
  }
})

defineExpose({
  getEditorView: () => view
})
</script>

<style scoped>
.code-editor-container {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  overflow: hidden;
}

/* Ensure CodeMirror takes full height of container */
:deep(.cm-editor) {
  height: 100%;
}
:deep(.cm-scroller) {
  overflow: auto;
}
</style>
