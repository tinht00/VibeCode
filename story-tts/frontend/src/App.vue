<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { api } from './lib/api'
import type {
  AppState,
  Chapter,
  ChapterContent,
  ImportFolderRequest,
  ProsodyPreset,
  ReaderProgress,
  RealtimeChapterPayload,
  RealtimeSession,
  RealtimeSessionState,
  RealtimeVoice,
  Story,
  StoryDetail
} from './types'

type PermissionMode = 'read' | 'readwrite'
type BrowserPermissionStatus = 'granted' | 'denied' | 'prompt'
type BrowserPermissionDescriptor = { mode?: PermissionMode }
type BrowserFileHandle = FileSystemFileHandle & { getFile(): Promise<File> }
type BrowserDirectoryHandle = FileSystemDirectoryHandle & {
  values(): AsyncIterable<FileSystemHandle>
  queryPermission(descriptor?: BrowserPermissionDescriptor): Promise<BrowserPermissionStatus>
  requestPermission(descriptor?: BrowserPermissionDescriptor): Promise<BrowserPermissionStatus>
}
type DirectoryPickerWindow = Window &
  typeof globalThis & {
    showDirectoryPicker?: (options?: { id?: string; mode?: 'read' | 'readwrite' }) => Promise<BrowserDirectoryHandle>
  }

type ImportedChapterDraft = {
  relativePath: string
  title: string
  content: string
}

type ImportedStoryDraft = {
  relativePath: string
  title: string
  chapters: ImportedChapterDraft[]
}

type ReaderBlock = {
  kind: 'heading' | 'body' | 'divider' | 'spacer'
  text: string
  normalizedLength: number
}

type LoadChapterOptions = {
  preservePlayback?: boolean
  skipPersist?: boolean
}

type RealtimeStatus = 'idle' | 'connecting' | 'buffering' | 'reading' | 'transitioning' | 'stopped' | 'finished' | 'error'

const presets: ProsodyPreset[] = ['stable', 'gentle', 'tense', 'climax']
const handleDbName = 'story-tts-reader'
const handleStoreName = 'directory-handles'
const handleKey = 'library-root'
const realtimePrefsKey = 'story-tts.realtime.controls.v1'
const edgeReadAloudPrefsKey = 'story-tts.edge-read-aloud.v1'

const loading = ref(false)
const error = ref('')
const state = ref<AppState | null>(null)
const stories = ref<Story[]>([])
const selectedStory = ref<StoryDetail | null>(null)
const selectedChapterId = ref<number | null>(null)
const chapterContent = ref<ChapterContent | null>(null)
const readerProgress = ref<ReaderProgress | null>(null)
const progressByStory = ref<Record<number, ReaderProgress>>({})
const currentPreset = ref<ProsodyPreset>('stable')

const realtimeVoices = ref<RealtimeVoice[]>([])
const selectedVoice = ref('')
const realtimeSpeed = ref(0)
const realtimePitch = ref(0)
const realtimeStatus = ref<RealtimeStatus>('idle')
const realtimeSession = ref<RealtimeSession | null>(null)
const realtimeCurrentChapterId = ref<number | null>(null)
const realtimeCurrentChapterTitle = ref('')
const realtimeError = ref('')
const realtimeServiceError = ref('')
const realtimeConnecting = ref(false)
const useEdgeReadAloud = ref(false)
const edgeReadAloudActive = ref(false)
const edgeReadAloudWordsPerMinute = ref(185)

const currentDirectoryHandle = ref<BrowserDirectoryHandle | null>(null)
const currentLibraryRoot = ref('')
const currentStreamMime = ref('audio/mpeg')

const folderInput = ref<HTMLInputElement | null>(null)
const readerBody = ref<HTMLElement | null>(null)
const audioRef = ref<HTMLAudioElement | null>(null)

const contentCache = new Map<number, ChapterContent>()
let progressTimer: number | null = null
let realtimeControlsSyncTimer: number | null = null
let realtimeRestartTimer: number | null = null
let activeSocket: WebSocket | null = null
let socketClosedByApp = false
let activeMediaSource: MediaSource | null = null
let activeSourceBuffer: SourceBuffer | null = null
let activeMediaUrl = ''
let queuedAudioChunks: Uint8Array[] = []
let pendingMediaEnd = false
let userPausedAudio = false
let edgeReadAloudTimer: number | null = null
const activeTab = ref<'library' | 'reader'>('library')
const activeReadingBlockIndex = ref(-1)
const audioCurrentTime = ref(0)
const audioDuration = ref(0)

const selectedChapter = computed<Chapter | null>(() => {
  if (!selectedStory.value || selectedChapterId.value === null) return null
  return selectedStory.value.chapters.find((chapter) => chapter.id === selectedChapterId.value) ?? null
})

const sortedStories = computed(() =>
  [...stories.value].sort((left, right) => {
    const leftTime = left.lastOpenedAt ? new Date(left.lastOpenedAt).getTime() : 0
    const rightTime = right.lastOpenedAt ? new Date(right.lastOpenedAt).getTime() : 0
    return rightTime - leftTime || left.title.localeCompare(right.title, 'vi')
  })
)

const recentStories = computed(() => sortedStories.value.filter((story) => story.lastOpenedAt).slice(0, 4))

const selectedChapterPosition = computed(() => {
  if (!selectedStory.value || !selectedChapter.value) return ''
  return `${selectedChapter.value.chapterIndex}/${selectedStory.value.chapters.length}`
})

const chapterWordCount = computed(() => {
  if (!chapterContent.value?.text) return 0
  return chapterContent.value.text.split(/\s+/).filter(Boolean).length
})
const showLegacyReadingHighlight = computed(() => !useEdgeReadAloud.value)
const isEdgeBrowser = computed(() => /Edg\//.test(window.navigator.userAgent))

const canRefreshLibrary = computed(() => Boolean(currentDirectoryHandle.value) || stories.value.length === 0)
const formattedChapterBlocks = computed(() =>
  formatChapterBlocks(
    chapterContent.value?.text ?? '',
    chapterContent.value?.storyTitle ?? '',
    chapterContent.value?.chapterTitle ?? ''
  )
)

const isRealtimeActive = computed(() =>
  realtimeSession.value !== null && ['connecting', 'buffering', 'reading', 'transitioning'].includes(realtimeStatus.value)
)

const realtimeVoiceOptions = computed(() =>
  [...realtimeVoices.value].sort((left, right) =>
    `${left.locale} ${left.friendlyName}`.localeCompare(`${right.locale} ${right.friendlyName}`, 'vi')
  )
)

const currentVoiceLabel = computed(() => {
  const matched = realtimeVoiceOptions.value.find((voice) => voice.id === selectedVoice.value)
  return matched?.friendlyName ?? selectedVoice.value ?? ''
})

const realtimeStatusLabel = computed(() => {
  switch (realtimeStatus.value) {
    case 'connecting':
      return 'Đang kết nối'
    case 'buffering':
      return 'Đang tải audio'
    case 'reading':
      return 'Đang đọc'
    case 'transitioning':
      return 'Đổi chương'
    case 'stopped':
      return 'Đã dừng'
    case 'finished':
      return 'Hoàn tất'
    case 'error':
      return 'Có lỗi'
    default:
      return 'Sẵn sàng'
  }
})

const realtimeStatusText = computed(() => {
  if (realtimeError.value) return realtimeError.value
  if (realtimeServiceError.value) return realtimeServiceError.value

  switch (realtimeStatus.value) {
    case 'connecting':
      return 'Đang mở phiên realtime TTS và kết nối stream audio...'
    case 'buffering':
      return `Đang nhận audio realtime cho ${realtimeCurrentChapterTitle.value || 'chương hiện tại'}.`
    case 'reading':
      return `Đang đọc ${realtimeCurrentChapterTitle.value || 'chương hiện tại'} và sẽ tự chuyển chương sau khi đọc xong.`
    case 'transitioning':
      return 'Đang chuyển sang chương kế tiếp...'
    case 'stopped':
      return 'Đã dừng phiên đọc realtime.'
    case 'finished':
      return 'Đã đọc hết truyện hiện tại.'
    case 'error':
      return 'Luồng realtime TTS gặp lỗi.'
    default:
      return 'Realtime TTS sẽ stream trực tiếp, không tạo file audio trung gian.'
  }
})

const currentStoryProgress = computed(() => {
  const storyId = selectedStory.value?.story.id
  if (!storyId) return null
  return progressByStory.value[storyId] ?? null
})

function formatDateTime(value?: string) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit'
  }).format(date)
}

function formatDuration(seconds: number) {
  if (isNaN(seconds) || seconds === Infinity) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function collateNatural(left: string, right: string) {
  return left.localeCompare(right, 'vi', { numeric: true, sensitivity: 'base' })
}

function formatChapterBlocks(text: string, storyTitle: string, chapterTitle: string): ReaderBlock[] {
  const rawNormalized = text.replace(/\u00a0/g, ' ').replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim()
  if (!rawNormalized) return []

  const blocks: ReaderBlock[] = []
  const lines = rawNormalized.split('\n')

  for (const line of lines) {
    const trimmedLine = line.trim()

    if (!trimmedLine) {
      if (blocks.at(-1)?.kind !== 'spacer') {
        blocks.push({ kind: 'spacer', text: '', normalizedLength: 0 })
      }
      continue
    }

    if (isDividerLine(trimmedLine)) {
      blocks.push({ kind: 'divider', text: trimmedLine, normalizedLength: 0 })
      continue
    }

    if (isHeadingLine(trimmedLine)) {
      blocks.push({ kind: 'heading', text: trimmedLine, normalizedLength: countNormalizedLength(trimmedLine) })
      continue
    }

    blocks.push({ kind: 'body', text: line, normalizedLength: countNormalizedLength(trimmedLine) })
  }

  return blocks
}

function isDividerLine(value: string) {
  return /^[-=_*~.]{5,}$/.test(value.replace(/\s+/g, ''))
}

function isHeadingLine(value: string) {
  return /^(chuong|chương|quyen|quyển|phan|phần|tap|tập)\b/i.test(value)
}

function normalizeTtsText(value: string) {
  return value
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[-=_*~]{5,}/g, ' ')
    .replace(/\s+([,.;:!?])/g, '$1')
    .replace(/\s+/g, ' ')
    .trim()
}

function countNormalizedLength(value: string) {
  const normalized = normalizeTtsText(value)
  return normalized ? normalized.length : 0
}

function openLegacyFolderPicker() {
  folderInput.value?.click()
}

async function refresh(preferredStoryId?: number, preferredStorySlug?: string) {
  loading.value = true
  error.value = ''
  try {
    const [nextState, nextStories] = await Promise.all([api.state(), api.stories()])
    state.value = nextState
    applyRealtimeDefaults(nextState)
    await ensureRealtimeVoices(nextState.config.realtimeTtsBaseUrl)

    stories.value = nextStories.items ?? []
    await hydrateStoryProgress(stories.value)
    if (stories.value.length === 0) {
      selectedStory.value = null
      selectedChapterId.value = null
      chapterContent.value = null
      readerProgress.value = null
      return
    }

    const targetStoryId = resolveStoryId(preferredStoryId, preferredStorySlug)
    if (targetStoryId) {
      await loadStory(targetStoryId)
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

async function hydrateStoryProgress(items: Story[]) {
  const entries = await Promise.all(
    items.map(async (story) => {
      try {
        const progress = await api.progress(story.id)
        return [story.id, progress.storyId ? progress : { storyId: story.id, chapterIndex: 0, scrollPercent: 0, audioPositionSec: 0 }] as const
      } catch {
        return [story.id, { storyId: story.id, chapterIndex: 0, scrollPercent: 0, audioPositionSec: 0 }] as const
      }
    })
  )

  progressByStory.value = Object.fromEntries(entries)
}

function applyRealtimeDefaults(appState: AppState) {
  const persisted = readRealtimePreferences()
  if (!selectedVoice.value) {
    selectedVoice.value = persisted.voice || appState.config.realtimeDefaultVoice || appState.config.edgeVoice
  }
  realtimeSpeed.value = persisted.speed ?? appState.config.realtimeDefaultSpeed
  realtimePitch.value = persisted.pitch ?? appState.config.realtimeDefaultPitch
}

function clampRealtimeSpeed(value: number) {
  return Math.max(-50, Math.min(50, Math.round(value)))
}

function clampRealtimePitch(value: number) {
  return Math.max(-80, Math.min(80, Math.round(value)))
}

function readRealtimePreferences(): { voice: string; speed?: number; pitch?: number } {
  try {
    const raw = window.localStorage.getItem(realtimePrefsKey)
    if (!raw) return { voice: '' }
    const parsed = JSON.parse(raw) as { voice?: string; speed?: number; pitch?: number }
    return {
      voice: typeof parsed.voice === 'string' ? parsed.voice : '',
      speed: typeof parsed.speed === 'number' ? clampRealtimeSpeed(parsed.speed) : undefined,
      pitch: typeof parsed.pitch === 'number' ? clampRealtimePitch(parsed.pitch) : undefined
    }
  } catch {
    return { voice: '' }
  }
}

function persistRealtimePreferences() {
  try {
    window.localStorage.setItem(
      realtimePrefsKey,
      JSON.stringify({
        voice: selectedVoice.value,
        speed: clampRealtimeSpeed(realtimeSpeed.value),
        pitch: clampRealtimePitch(realtimePitch.value)
      })
    )
  } catch {
    // Bỏ qua lỗi localStorage (quota/private mode), không chặn luồng đọc.
  }
}

async function ensureRealtimeVoices(baseUrl?: string) {
  const targetBaseUrl = baseUrl || state.value?.config.realtimeTtsBaseUrl
  if (!targetBaseUrl) return

  try {
    const payload = await api.realtimeVoices(targetBaseUrl)
    realtimeVoices.value = payload.items ?? []
    realtimeServiceError.value = ''

    const preferredVoice = selectedVoice.value || payload.defaultVoice || state.value?.config.realtimeDefaultVoice || ''
    const matched = realtimeVoices.value.find((voice) => voice.id === preferredVoice) ?? realtimeVoices.value[0]
    selectedVoice.value = matched?.id ?? preferredVoice
  } catch (err) {
    realtimeServiceError.value = err instanceof Error ? err.message : String(err)
  }
}

function resolveStoryId(preferredStoryId?: number, preferredStorySlug?: string) {
  if (preferredStoryId) return preferredStoryId
  if (preferredStorySlug) {
    const matched = stories.value.find((story) => story.slug === preferredStorySlug)
    if (matched) return matched.id
  }
  if (selectedStory.value) {
    const byId = stories.value.find((story) => story.id === selectedStory.value?.story.id)
    if (byId) return byId.id
    const bySlug = stories.value.find((story) => story.slug === selectedStory.value?.story.slug)
    if (bySlug) return bySlug.id
  }
  return sortedStories.value[0]?.id
}

async function importFromFolder(event: Event) {
  const target = event.target as HTMLInputElement | null
  const files = Array.from(target?.files ?? [])
  if (files.length === 0) return

  try {
    const payload = await buildImportPayloadFromFiles(files)
    currentDirectoryHandle.value = null
    currentLibraryRoot.value = payload.rootName
    await importPayload(payload)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    if (target) {
      target.value = ''
    }
    loading.value = false
  }
}

async function buildImportPayloadFromFiles(files: File[]): Promise<ImportFolderRequest> {
  const txtFiles = files.filter((file) => file.name.toLowerCase().endsWith('.txt') && file.webkitRelativePath)
  if (txtFiles.length === 0) {
    throw new Error('Không tìm thấy file .txt hợp lệ trong thư mục đã chọn')
  }

  const rootName = txtFiles[0].webkitRelativePath.split('/')[0] || 'library'
  const storyMap = new Map<string, { title: string; chapters: Array<{ relativePath: string; title: string; file: File }> }>()

  for (const file of txtFiles) {
    const segments = file.webkitRelativePath.split('/').filter(Boolean)
    if (segments.length !== 3) continue
    const [, storyDir, chapterFile] = segments
    const storyBucket = storyMap.get(storyDir) ?? { title: storyDir, chapters: [] }
    storyBucket.chapters.push({
      relativePath: `${storyDir}/${chapterFile}`,
      title: chapterFile.replace(/\.txt$/i, ''),
      file
    })
    storyMap.set(storyDir, storyBucket)
  }

  if (storyMap.size === 0) {
    throw new Error('Cần chọn thư mục gốc có cấu trúc: thư_mục_gốc/truyện/chương.txt')
  }

  const storiesPayload: ImportedStoryDraft[] = []
  for (const [relativePath, storyEntry] of [...storyMap.entries()].sort((left, right) => collateNatural(left[0], right[0]))) {
    const chapters = await Promise.all(
      storyEntry.chapters
        .sort((left, right) => collateNatural(left.relativePath, right.relativePath))
        .map(async (chapter) => ({
          relativePath: chapter.relativePath,
          title: chapter.title,
          content: await chapter.file.text()
        }))
    )

    storiesPayload.push({ relativePath, title: storyEntry.title, chapters })
  }

  return { rootName, stories: storiesPayload }
}

async function chooseLibraryFolder() {
  const pickerWindow = window as DirectoryPickerWindow
  if (!pickerWindow.showDirectoryPicker) {
    openLegacyFolderPicker()
    return
  }

  try {
    const handle = await pickerWindow.showDirectoryPicker({ id: 'story-tts-library', mode: 'read' })
    if (!(await ensureDirectoryPermission(handle, true))) {
      throw new Error('Chưa có quyền đọc thư mục đã chọn')
    }
    currentDirectoryHandle.value = handle
    currentLibraryRoot.value = handle.name
    await saveDirectoryHandle(handle)
    await importFromDirectoryHandle(handle)
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      return
    }
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function importFromDirectoryHandle(handle: BrowserDirectoryHandle) {
  const storiesPayload: ImportedStoryDraft[] = []

  for await (const entry of handle.values()) {
    if (entry.kind !== 'directory') continue
    const storyHandle = entry as BrowserDirectoryHandle
    const chapters: ImportedChapterDraft[] = []

    for await (const child of storyHandle.values()) {
      if (child.kind !== 'file' || !child.name.toLowerCase().endsWith('.txt')) continue
      const file = await (child as BrowserFileHandle).getFile()
      chapters.push({
        relativePath: `${storyHandle.name}/${child.name}`,
        title: child.name.replace(/\.txt$/i, ''),
        content: await file.text()
      })
    }

    if (chapters.length === 0) continue
    storiesPayload.push({
      relativePath: storyHandle.name,
      title: storyHandle.name,
      chapters: chapters.sort((left, right) => collateNatural(left.relativePath, right.relativePath))
    })
  }

  if (storiesPayload.length === 0) {
    throw new Error('Không tìm thấy chương .txt trực tiếp bên trong các thư mục truyện')
  }

  storiesPayload.sort((left, right) => collateNatural(left.relativePath, right.relativePath))
  currentLibraryRoot.value = handle.name
  await importPayload({ rootName: handle.name, stories: storiesPayload })
}

async function importPayload(payload: ImportFolderRequest) {
  loading.value = true
  error.value = ''

  try {
    const previousStorySlug = selectedStory.value?.story.slug
    const snapshot = await api.importFolder(payload)
    stories.value = snapshot.stories ?? []
    const preferredStoryId = resolveStoryId(undefined, previousStorySlug)
    await refresh(preferredStoryId, previousStorySlug)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
    throw err
  } finally {
    loading.value = false
  }
}

async function refreshLibrary() {
  error.value = ''
  try {
    if (currentDirectoryHandle.value) {
      const granted = await ensureDirectoryPermission(currentDirectoryHandle.value, true)
      if (!granted) {
        error.value = 'Không còn quyền truy cập thư mục đã chọn. Hãy chọn lại thư mục truyện.'
        return
      }
      await importFromDirectoryHandle(currentDirectoryHandle.value)
      return
    }

    if (stories.value.length > 0) {
      error.value = 'Trình duyệt chưa giữ quyền thư mục. Hãy bấm "Chọn thư mục truyện" lại một lần để app có thể làm mới tự động.'
      return
    }

    await refresh()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
}

async function ensureDirectoryPermission(handle: BrowserDirectoryHandle, ask: boolean) {
  const options = { mode: 'read' as const }
  if ((await handle.queryPermission(options)) === 'granted') {
    return true
  }
  if (!ask) return false
  return (await handle.requestPermission(options)) === 'granted'
}

async function restoreDirectoryHandle() {
  const handle = await loadDirectoryHandle()
  if (!handle) return
  const granted = await ensureDirectoryPermission(handle, false)
  if (!granted) return
  currentDirectoryHandle.value = handle
  currentLibraryRoot.value = handle.name
}

function openHandleDb() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = window.indexedDB.open(handleDbName, 1)
    request.onerror = () => reject(request.error ?? new Error('Không mở được IndexedDB cho handle thư mục'))
    request.onupgradeneeded = () => {
      request.result.createObjectStore(handleStoreName)
    }
    request.onsuccess = () => resolve(request.result)
  })
}

async function saveDirectoryHandle(handle: BrowserDirectoryHandle) {
  const db = await openHandleDb()
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(handleStoreName, 'readwrite')
    tx.objectStore(handleStoreName).put(handle, handleKey)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error ?? new Error('Không lưu được handle thư mục'))
    tx.onabort = () => reject(tx.error ?? new Error('Không lưu được handle thư mục'))
  })
  db.close()
}

async function loadDirectoryHandle() {
  if (!window.indexedDB) return null
  const db = await openHandleDb()
  const result = await new Promise<BrowserDirectoryHandle | null>((resolve, reject) => {
    const tx = db.transaction(handleStoreName, 'readonly')
    const request = tx.objectStore(handleStoreName).get(handleKey)
    request.onsuccess = () => resolve((request.result as BrowserDirectoryHandle | undefined) ?? null)
    request.onerror = () => reject(request.error ?? new Error('Không đọc được handle thư mục đã lưu'))
  })
  db.close()
  return result
}

async function loadStory(storyId: number) {
  await stopRealtimePlayback({ quiet: true, clearSession: true })
  loading.value = true
  error.value = ''
  try {
    const [detail, progress] = await Promise.all([api.story(storyId), api.progress(storyId)])
    selectedStory.value = detail
    readerProgress.value = progress.storyId ? progress : null
    progressByStory.value = {
      ...progressByStory.value,
      [storyId]: progress.storyId ? progress : { storyId, chapterIndex: 0, scrollPercent: 0, audioPositionSec: 0 }
    }
    currentPreset.value = detail.story.defaultPreset || 'stable'
    contentCache.clear()

    const preferredChapter = detail.chapters.find((chapter) => chapter.chapterIndex === progress.chapterIndex) ?? detail.chapters[0]
    if (preferredChapter) {
      await loadChapter(preferredChapter.id, progress.chapterIndex === preferredChapter.chapterIndex ? progress : null)
    } else {
      selectedChapterId.value = null
      chapterContent.value = null
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

function storyProgress(storyId: number) {
  return progressByStory.value[storyId] ?? null
}

function storyProgressText(story: Story) {
  const progress = storyProgress(story.id)
  if (!progress?.chapterIndex) {
    return 'Chưa có tiến độ đọc'
  }
  return `Đang đọc tới chương ${progress.chapterIndex}/${story.chapterCount}`
}

function storyContinueText(story: Story) {
  const progress = storyProgress(story.id)
  if (!progress?.chapterIndex) {
    return 'Bắt đầu đọc'
  }
  const nextChapter = Math.min(progress.chapterIndex, story.chapterCount)
  return `Đọc tiếp chương ${nextChapter}`
}

async function openStoryReader(storyId: number) {
  activeTab.value = 'reader'
  await loadStory(storyId)
}

async function continueStory(storyId: number, event?: Event) {
  event?.stopPropagation()
  activeTab.value = 'reader'
  await loadStory(storyId)
}

async function loadChapter(chapterId: number, progress?: ReaderProgress | null, options: LoadChapterOptions & { switchTab?: boolean } = {}) {
  if (options.switchTab) {
    activeTab.value = 'reader'
  }
  if (!options.preservePlayback) {
    if (edgeReadAloudActive.value) {
      await stopEdgeReadAloudPlayback()
    } else {
      clearEdgeReadAloudTimer()
    }
    await stopRealtimePlayback({ quiet: true, clearSession: true })
  }

  loading.value = true
  error.value = ''
  try {
    const content = await getChapterContentCached(chapterId)
    selectedChapterId.value = chapterId
    chapterContent.value = content
    await nextTick()
    restoreReaderPosition(progress)
    if (!options.skipPersist) {
      await persistProgress(0)
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

async function getChapterContentCached(chapterId: number) {
  const cached = contentCache.get(chapterId)
  if (cached) return cached
  const content = await api.chapterContent(chapterId)
  contentCache.set(chapterId, content)
  return content
}

function restoreReaderPosition(progress?: ReaderProgress | null) {
  const chapter = selectedChapter.value
  const container = readerBody.value
  if (!chapter || !container) return

  if (progress && progress.chapterIndex === chapter.chapterIndex) {
    const maxScroll = Math.max(container.scrollHeight - container.clientHeight, 0)
    container.scrollTop = maxScroll * progress.scrollPercent
  } else {
    container.scrollTop = 0
  }
}

function currentScrollPercent() {
  const container = readerBody.value
  if (!container) return 0
  const maxScroll = container.scrollHeight - container.clientHeight
  if (maxScroll <= 0) return 0
  return container.scrollTop / maxScroll
}

async function persistProgress(audioPositionSec = 0) {
  const story = selectedStory.value?.story
  const chapter = selectedChapter.value
  if (!story || !chapter) return

  const payload: ReaderProgress = {
    storyId: story.id,
    chapterIndex: chapter.chapterIndex,
    scrollPercent: currentScrollPercent(),
    audioPositionSec
  }

  const saved = await api.saveProgress(payload)
  readerProgress.value = saved
  progressByStory.value = {
    ...progressByStory.value,
    [story.id]: saved
  }
  stories.value = stories.value.map((item) =>
    item.id === story.id ? { ...item, lastOpenedAt: saved.updatedAt ?? new Date().toISOString() } : item
  )
}

function scheduleProgressSave() {
  if (progressTimer !== null) {
    window.clearTimeout(progressTimer)
  }
  progressTimer = window.setTimeout(() => {
    void persistProgress(audioRef.value?.currentTime ?? 0)
  }, 350)
}

function clearEdgeReadAloudTimer() {
  if (edgeReadAloudTimer !== null) {
    window.clearTimeout(edgeReadAloudTimer)
    edgeReadAloudTimer = null
  }
}

function persistEdgeReadAloudPreferences() {
  window.localStorage.setItem(
    edgeReadAloudPrefsKey,
    JSON.stringify({
      enabled: useEdgeReadAloud.value,
      wordsPerMinute: edgeReadAloudWordsPerMinute.value
    })
  )
}

function focusReaderForEdgeReadAloud() {
  if (!readerBody.value) return
  readerBody.value.scrollTop = 0
  readerBody.value.focus({ preventScroll: true })

  const firstReadable = readerBody.value.querySelector('.reader-paragraph, .reader-heading, .reader-divider') as HTMLElement | null
  if (!firstReadable) return

  const selection = window.getSelection()
  if (!selection) return

  const walker = document.createTreeWalker(firstReadable, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      return node.textContent?.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP
    }
  })
  const firstTextNode = walker.nextNode()
  if (!firstTextNode) return

  const range = document.createRange()
  range.setStart(firstTextNode, 0)
  range.setEnd(firstTextNode, firstTextNode.textContent?.length ?? 0)
  selection.removeAllRanges()
  selection.addRange(range)
}

async function triggerEdgeReadAloudHotkey() {
  await nextTick()
  focusReaderForEdgeReadAloud()
  await new Promise((resolve) => window.setTimeout(resolve, 180))
  await api.toggleEdgeReadAloud()
}

function scheduleEdgeReadAloudAutoNext() {
  clearEdgeReadAloudTimer()
  if (!edgeReadAloudActive.value || !selectedChapter.value) return

  const estimatedMs = Math.max(12000, Math.round((chapterWordCount.value / Math.max(edgeReadAloudWordsPerMinute.value, 120)) * 60_000 + 4000))
  edgeReadAloudTimer = window.setTimeout(async () => {
    if (!edgeReadAloudActive.value) return
    const target = chapterAt(1)
    if (!target) {
      edgeReadAloudActive.value = false
      return
    }
    await loadChapter(target.id, null, { preservePlayback: true })
    await triggerEdgeReadAloudHotkey()
    scheduleEdgeReadAloudAutoNext()
  }, estimatedMs)
}

async function startEdgeReadAloudPlayback() {
  if (!isEdgeBrowser.value) {
    error.value = 'Edge Read Aloud mode chỉ dùng được trong Microsoft Edge.'
    return
  }
  if (!chapterContent.value) return

  await stopRealtimePlayback({ quiet: true, clearSession: true })
  error.value = ''
  edgeReadAloudActive.value = true
  activeReadingBlockIndex.value = -1
  await triggerEdgeReadAloudHotkey()
  scheduleEdgeReadAloudAutoNext()
}

async function stopEdgeReadAloudPlayback() {
  clearEdgeReadAloudTimer()
  if (!edgeReadAloudActive.value) return
  edgeReadAloudActive.value = false
  activeReadingBlockIndex.value = -1
  await triggerEdgeReadAloudHotkey()
}

function handleTimeUpdate() {
  if (audioRef.value) {
    audioCurrentTime.value = audioRef.value.currentTime
    audioDuration.value = audioRef.value.duration
  }
  scheduleProgressSave()
  updateActiveReadingBlock()
}

function togglePlayback() {
  if (useEdgeReadAloud.value) {
    if (edgeReadAloudActive.value) {
      void stopEdgeReadAloudPlayback()
    } else {
      void startEdgeReadAloudPlayback()
    }
    return
  }

  if (!audioRef.value) return
  
  if (!realtimeSession.value && !realtimeConnecting.value) {
    void startRealtimePlayback()
    return
  }

  if (audioRef.value.paused) {
    userPausedAudio = false
    audioRef.value.play()
  } else {
    userPausedAudio = true
    audioRef.value.pause()
  }
}

function seekAudio(event: MouseEvent) {
  const container = event.currentTarget as HTMLElement
  if (!container || !audioRef.value) return
  const rect = container.getBoundingClientRect()
  const percent = (event.clientX - rect.left) / rect.width
  const seekTime = percent * (audioRef.value.duration || 0)
  audioRef.value.currentTime = seekTime
}

function updateActiveReadingBlock() {
  if (useEdgeReadAloud.value) {
    activeReadingBlockIndex.value = -1
    return
  }
  if (!audioRef.value || realtimeStatus.value === 'stopped' || !isRealtimeActive.value) {
    activeReadingBlockIndex.value = -1
    return
  }

  const blocks = formattedChapterBlocks.value
  if (blocks.length === 0) {
    activeReadingBlockIndex.value = -1
    return
  }

  const totalChars = blocks.reduce((sum, block) => sum + block.normalizedLength, 0)
  let currentChars = 0

  if (audioRef.value.duration && Number.isFinite(audioRef.value.duration) && audioRef.value.duration > 0 && totalChars > 0) {
    const ratio = Math.min(1, Math.max(0, audioRef.value.currentTime / audioRef.value.duration))
    currentChars = ratio * totalChars
  } else {
    const speedRatio = 1 + (realtimeSpeed.value / 100)
    const charsPerSecond = 22 * speedRatio
    currentChars = audioRef.value.currentTime * charsPerSecond
  }

  let accumulated = 0
  let targetIndex = -1

  for (let i = 0; i < blocks.length; i++) {
    const blockLength = blocks[i].normalizedLength
    if (accumulated + blockLength >= currentChars) {
      targetIndex = i
      break
    }
    accumulated += blockLength
  }

  if (targetIndex === -1 && currentChars > 0 && blocks.length > 0) {
    targetIndex = blocks.length - 1
  }

  if (activeReadingBlockIndex.value !== targetIndex) {
    activeReadingBlockIndex.value = targetIndex
    autoScrollToActiveBlock()
  }
}

function autoScrollToActiveBlock() {
  if (activeReadingBlockIndex.value === -1 || !readerBody.value) return
  const el = readerBody.value.children[activeReadingBlockIndex.value] as HTMLElement
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

async function buildRealtimePayload() {
  if (!selectedStory.value || !selectedChapter.value) {
    throw new Error('Chưa có chương để phát realtime')
  }

  const chapters = await Promise.all(
    selectedStory.value.chapters.map(async (chapter) => {
      const content = await getChapterContentCached(chapter.id)
      return {
        chapterId: content.chapterId,
        chapterIndex: content.chapterIndex,
        title: content.chapterTitle,
        text: content.text
      } satisfies RealtimeChapterPayload
    })
  )

  return {
    storyId: selectedStory.value.story.id,
    chapterId: selectedChapter.value.id,
    chapters,
    voice: selectedVoice.value,
    speed: realtimeSpeed.value,
    pitch: realtimePitch.value,
    autoNext: true
  }
}

function realtimeBaseUrl() {
  return state.value?.config.realtimeTtsBaseUrl ?? ''
}

function websocketUrl(baseUrl: string, sessionId: string) {
  const url = new URL(baseUrl)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = `${url.pathname.replace(/\/$/, '')}/sessions/${sessionId}/stream`
  return url.toString()
}

async function startRealtimePlayback() {
  if (!selectedStory.value || !selectedChapter.value) return
  const baseUrl = realtimeBaseUrl()
  if (!baseUrl) {
    error.value = 'Thiếu cấu hình realtime TTS base URL từ backend Go.'
    return
  }

  if (realtimeVoices.value.length === 0) {
    await ensureRealtimeVoices(baseUrl)
  }
  if (!selectedVoice.value) {
    error.value = 'Chưa có voice realtime hợp lệ.'
    return
  }

  realtimeError.value = ''
  realtimeConnecting.value = true
  userPausedAudio = false
  error.value = ''

  try {
    await stopRealtimePlayback({ quiet: true, clearSession: true })
    realtimeStatus.value = 'connecting'
    await prepareRealtimeMediaStream()
    const payload = await buildRealtimePayload()
    const session = await api.createRealtimeSession(baseUrl, payload)
    realtimeSession.value = session
    realtimeCurrentChapterId.value = session.chapterId
    realtimeCurrentChapterTitle.value = selectedChapter.value.title
    connectRealtimeSocket(baseUrl, session.id)
  } catch (err) {
    realtimeStatus.value = 'error'
    realtimeError.value = err instanceof Error ? err.message : String(err)
    error.value = realtimeError.value
    teardownRealtimeSocket()
    resetRealtimeMediaStream()
  } finally {
    realtimeConnecting.value = false
  }
}

async function restartRealtimePlayback() {
  await startRealtimePlayback()
}

function clearRealtimeControlSyncTimer() {
  if (realtimeControlsSyncTimer !== null) {
    window.clearTimeout(realtimeControlsSyncTimer)
    realtimeControlsSyncTimer = null
  }
}

function clearRealtimeRestartTimer() {
  if (realtimeRestartTimer !== null) {
    window.clearTimeout(realtimeRestartTimer)
    realtimeRestartTimer = null
  }
}

async function syncRealtimeControls() {
  const baseUrl = realtimeBaseUrl()
  const sessionId = realtimeSession.value?.id
  if (!baseUrl || !sessionId) return

  try {
    const updated = await api.updateRealtimeControls(baseUrl, sessionId, {
      voice: selectedVoice.value,
      speed: realtimeSpeed.value,
      pitch: realtimePitch.value,
      autoNext: realtimeSession.value?.autoNext ?? true
    })
    realtimeSession.value = updated
    realtimeServiceError.value = ''
  } catch (err) {
    realtimeServiceError.value = err instanceof Error ? err.message : String(err)
  }
}

function scheduleRealtimeControlsSync() {
  if (!realtimeSession.value || realtimeConnecting.value) return
  clearRealtimeControlSyncTimer()
  // Debounce để không spam API khi người dùng kéo slider liên tục.
  realtimeControlsSyncTimer = window.setTimeout(() => {
    void syncRealtimeControls()
  }, 180)
}

function scheduleRealtimeRestart() {
  if (!realtimeSession.value || realtimeConnecting.value) return
  clearRealtimeRestartTimer()
  // Khi đang đọc, restart phiên realtime để chương/đoạn tiếp theo áp dụng tốc độ/cao độ mới ngay.
  realtimeRestartTimer = window.setTimeout(() => {
    if (isRealtimeActive.value) {
      void restartRealtimePlayback()
      return
    }
    void syncRealtimeControls()
  }, 260)
}

async function stopRealtimePlayback(options: { quiet?: boolean; clearSession?: boolean } = {}) {
  clearRealtimeControlSyncTimer()
  clearRealtimeRestartTimer()
  const baseUrl = realtimeBaseUrl()
  const sessionId = realtimeSession.value?.id

  if (sessionId && baseUrl && !options.quiet) {
    try {
      await api.stopRealtimeSession(baseUrl, sessionId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
    }
  }

  teardownRealtimeSocket()
  finishRealtimeStream()
  if (options.clearSession) {
    realtimeSession.value = null
    realtimeCurrentChapterId.value = null
    realtimeCurrentChapterTitle.value = ''
    realtimeStatus.value = 'stopped'
  }
  await persistProgress(0).catch(() => undefined)
}

async function prepareRealtimeMediaStream() {
  resetRealtimeMediaStream()

  if (!window.MediaSource || !MediaSource.isTypeSupported('audio/mpeg')) {
    throw new Error('Trình duyệt hiện tại không hỗ trợ MediaSource cho audio/mpeg realtime.')
  }

  if (!audioRef.value) {
    await nextTick()
  }
  if (!audioRef.value) {
    throw new Error('Không khởi tạo được audio player realtime.')
  }

  activeMediaSource = new MediaSource()
  activeMediaUrl = URL.createObjectURL(activeMediaSource)
  currentStreamMime.value = 'audio/mpeg'
  pendingMediaEnd = false
  queuedAudioChunks = []

  activeMediaSource.addEventListener('sourceopen', handleSourceOpen, { once: true })
  audioRef.value.src = activeMediaUrl
  audioRef.value.autoplay = false
  audioRef.value.load()
}

function handleSourceOpen() {
  if (!activeMediaSource || activeMediaSource.readyState !== 'open') return
  activeSourceBuffer = activeMediaSource.addSourceBuffer(currentStreamMime.value)
  activeSourceBuffer.mode = 'sequence'
  activeSourceBuffer.addEventListener('updateend', flushAudioChunkQueue)
  flushAudioChunkQueue()
}

function appendRealtimeChunk(data: ArrayBuffer) {
  queuedAudioChunks.push(new Uint8Array(data.slice(0)))
  if (realtimeStatus.value === 'connecting') {
    realtimeStatus.value = 'buffering'
  }
  flushAudioChunkQueue()
}

function isSourceBufferAttached(sourceBuffer: SourceBuffer) {
  if (!activeMediaSource || activeMediaSource.readyState !== 'open') return false
  try {
    return Array.from(activeMediaSource.sourceBuffers).includes(sourceBuffer)
  } catch {
    return false
  }
}

function flushAudioChunkQueue() {
  const sourceBuffer = activeSourceBuffer
  if (!sourceBuffer || !isSourceBufferAttached(sourceBuffer)) return

  try {
    if (sourceBuffer.updating) return
  } catch {
    return
  }

  if (audioRef.value?.paused && !userPausedAudio) {
    let bufferedSeconds = 0
    try {
      if (sourceBuffer.buffered.length > 0) {
        bufferedSeconds = sourceBuffer.buffered.end(sourceBuffer.buffered.length - 1)
      }
    } catch {
      bufferedSeconds = 0
    }
    if (bufferedSeconds >= 4 || pendingMediaEnd) {
      void audioRef.value.play().catch(() => undefined)
    }
  }

  if (queuedAudioChunks.length > 0) {
    const chunk = queuedAudioChunks.shift()
    if (!chunk) return
    const buffer = chunk.buffer.slice(chunk.byteOffset, chunk.byteOffset + chunk.byteLength) as ArrayBuffer
    try {
      sourceBuffer.appendBuffer(buffer)
    } catch {
      // Có thể bị teardown đúng lúc append; bỏ qua để tránh lỗi runtime.
    }
    return
  }

  if (pendingMediaEnd && activeMediaSource && activeMediaSource.readyState === 'open') {
    try {
      activeMediaSource.endOfStream()
    } catch {
      // Bỏ qua nếu MediaSource đã tự kết thúc.
    }
  }
}

function finishRealtimeStream() {
  pendingMediaEnd = true
  flushAudioChunkQueue()
}

function resetRealtimeMediaStream() {
  pendingMediaEnd = false
  queuedAudioChunks = []
  userPausedAudio = false

  if (activeSourceBuffer) {
    activeSourceBuffer.removeEventListener('updateend', flushAudioChunkQueue)
    try {
      if (activeMediaSource?.readyState === 'open') {
        activeSourceBuffer.abort()
      }
    } catch {
      // Ignore abort errors while tearing down the stream.
    }
  }

  if (audioRef.value) {
    audioRef.value.pause()
    audioRef.value.removeAttribute('src')
    audioRef.value.load()
  }

  if (activeMediaUrl) {
    URL.revokeObjectURL(activeMediaUrl)
  }

  activeSourceBuffer = null
  activeMediaSource = null
  activeMediaUrl = ''
}

function connectRealtimeSocket(baseUrl: string, sessionId: string) {
  teardownRealtimeSocket()
  socketClosedByApp = false

  const socket = new WebSocket(websocketUrl(baseUrl, sessionId))
  socket.binaryType = 'arraybuffer'
  activeSocket = socket

  socket.onmessage = async (event) => {
    if (typeof event.data === 'string') {
      handleRealtimeEvent(JSON.parse(event.data) as RealtimeSessionState)
      return
    }

    const buffer = event.data instanceof Blob ? await event.data.arrayBuffer() : (event.data as ArrayBuffer)
    appendRealtimeChunk(buffer)
  }

  socket.onerror = () => {
    if (socketClosedByApp) return
    realtimeStatus.value = 'error'
    realtimeError.value = 'Kết nối WebSocket realtime TTS bị lỗi.'
  }

  socket.onclose = () => {
    activeSocket = null
    if (!socketClosedByApp && !['finished', 'stopped'].includes(realtimeStatus.value)) {
      realtimeStatus.value = 'error'
      realtimeError.value ||= 'Luồng realtime TTS đã ngắt kết nối.'
    }
    finishRealtimeStream()
  }
}

function teardownRealtimeSocket() {
  if (!activeSocket) return
  socketClosedByApp = true
  activeSocket.close()
  activeSocket = null
}

function handleRealtimeEvent(event: RealtimeSessionState) {
  if (event.type === 'audio_format' && event.mime) {
    currentStreamMime.value = event.mime
    return
  }

  switch (event.type) {
    case 'controls_updated':
      if (realtimeSession.value) {
        realtimeSession.value = {
          ...realtimeSession.value,
          voice: event.voice ?? realtimeSession.value.voice,
          speed: event.speed ?? realtimeSession.value.speed,
          pitch: event.pitch ?? realtimeSession.value.pitch,
          autoNext: event.autoNext ?? realtimeSession.value.autoNext
        }
      }
      break
    case 'session_started':
      realtimeStatus.value = 'buffering'
      realtimeError.value = ''
      break
    case 'chapter_started':
      realtimeStatus.value = 'reading'
      realtimeCurrentChapterId.value = event.chapterId ?? null
      realtimeCurrentChapterTitle.value = event.chapterTitle ?? ''
      if (event.chapterId) {
        void loadChapter(event.chapterId, null, { preservePlayback: true })
      }
      break
    case 'chapter_finished':
      realtimeStatus.value = 'transitioning'
      void persistProgress(0)
      break
    case 'chapter_transition':
      realtimeStatus.value = 'transitioning'
      break
    case 'story_finished':
      realtimeStatus.value = 'finished'
      finishRealtimeStream()
      break
    case 'stopped':
      realtimeStatus.value = 'stopped'
      finishRealtimeStream()
      break
    case 'stream_closed':
      if (!['finished', 'stopped', 'error'].includes(realtimeStatus.value)) {
        realtimeStatus.value = event.status === 'completed' ? 'finished' : 'stopped'
      }
      finishRealtimeStream()
      break
    case 'error':
      realtimeStatus.value = 'error'
      realtimeError.value = event.message || 'Realtime TTS gặp lỗi.'
      error.value = realtimeError.value
      finishRealtimeStream()
      break
  }
}

function chapterAt(offset: number) {
  if (!selectedStory.value || !selectedChapter.value) return null
  const currentIndex = selectedStory.value.chapters.findIndex((chapter) => chapter.id === selectedChapter.value?.id)
  return selectedStory.value.chapters[currentIndex + offset] ?? null
}

async function goToSiblingChapter(offset: number) {
  const target = chapterAt(offset)
  if (!target) return

  const shouldResumeRealtime = isRealtimeActive.value
  const shouldResumeEdgeReadAloud = edgeReadAloudActive.value
  if (shouldResumeEdgeReadAloud) {
    await stopEdgeReadAloudPlayback()
  }
  await loadChapter(target.id, null)
  if (shouldResumeRealtime) {
    await startRealtimePlayback()
  }
  if (shouldResumeEdgeReadAloud) {
    await startEdgeReadAloudPlayback()
  }
}

watch(selectedVoice, () => {
  persistRealtimePreferences()
  scheduleRealtimeControlsSync()
})

watch(realtimeSpeed, () => {
  realtimeSpeed.value = clampRealtimeSpeed(realtimeSpeed.value)
  persistRealtimePreferences()
  scheduleRealtimeRestart()
})

watch(realtimePitch, () => {
  realtimePitch.value = clampRealtimePitch(realtimePitch.value)
  persistRealtimePreferences()
  scheduleRealtimeRestart()
})

watch(useEdgeReadAloud, () => {
  if (!isEdgeBrowser.value && useEdgeReadAloud.value) {
    useEdgeReadAloud.value = false
    error.value = 'Edge Read Aloud mode chỉ dùng được trong Microsoft Edge.'
  }
  persistEdgeReadAloudPreferences()
})

watch(edgeReadAloudWordsPerMinute, () => {
  edgeReadAloudWordsPerMinute.value = Math.min(260, Math.max(120, Math.round(edgeReadAloudWordsPerMinute.value || 185)))
  persistEdgeReadAloudPreferences()
  if (edgeReadAloudActive.value) {
    scheduleEdgeReadAloudAutoNext()
  }
})

onMounted(() => {
  try {
    const raw = window.localStorage.getItem(edgeReadAloudPrefsKey)
    if (raw) {
      const parsed = JSON.parse(raw) as { enabled?: boolean; wordsPerMinute?: number }
      useEdgeReadAloud.value = Boolean(parsed.enabled)
      edgeReadAloudWordsPerMinute.value = Math.min(260, Math.max(120, Math.round(parsed.wordsPerMinute ?? 185)))
    }
  } catch {
    useEdgeReadAloud.value = false
    edgeReadAloudWordsPerMinute.value = 185
  }
  void restoreDirectoryHandle()
  void refresh()
})

onUnmounted(() => {
  clearEdgeReadAloudTimer()
  clearRealtimeControlSyncTimer()
  clearRealtimeRestartTimer()
  if (progressTimer !== null) {
    window.clearTimeout(progressTimer)
  }
  void stopRealtimePlayback({ quiet: true, clearSession: true })
})
</script>

<template>
  <main class="app-shell" :class="{ 'edge-read-aloud-shell': activeTab === 'reader' && useEdgeReadAloud }">
    <input
      ref="folderInput"
      class="hidden-input"
      type="file"
      webkitdirectory
      directory
      multiple
      @change="importFromFolder"
    />

    <header class="app-header panel" :class="{ 'edge-read-aloud-hidden': activeTab === 'reader' && useEdgeReadAloud }">
      <div class="branding">
        <div class="logo-icon">📚</div>
        <div>
          <h1 class="app-title">Story-TTS Reader</h1>
          <p class="app-subtitle">Thư viện truyện local, đọc tiếp nhanh và nghe realtime TTS</p>
        </div>
      </div>

      <div class="header-actions">
        <button class="ghost-button" @click="refreshLibrary" :disabled="loading || !canRefreshLibrary">Làm mới thư viện</button>
        <button @click="chooseLibraryFolder" :disabled="loading">Chọn thư mục truyện</button>
      </div>
    </header>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <nav class="app-tabs" :class="{ 'edge-read-aloud-hidden': activeTab === 'reader' && useEdgeReadAloud }">
      <button :class="{ active: activeTab === 'library' }" @click="activeTab = 'library'">📋 Quản lý Thư viện</button>
      <button :class="{ active: activeTab === 'reader' }" @click="activeTab = 'reader'" :disabled="!selectedStory">📖 Trình phát & Đọc chữ</button>
    </nav>

    <section v-if="activeTab === 'library'" class="workspace library-workspace">
      <div class="library-main">
        <section class="library-summary panel">
          <div class="sidebar-head">
            <div>
              <p class="eyebrow">Thư viện</p>
              <h2>{{ stories.length }} truyện</h2>
            </div>
            <p v-if="state" class="meta">Voice mặc định: {{ state.config.realtimeDefaultVoice }}</p>
          </div>

          <p v-if="currentLibraryRoot" class="meta library-root">Đang theo dõi: {{ currentLibraryRoot }}</p>

          <div v-if="recentStories.length" class="recent-strip">
            <button v-for="story in recentStories" :key="`recent-${story.id}`" class="recent-chip" @click="openStoryReader(story.id)">
              {{ story.title }}
            </button>
          </div>
        </section>

        <section class="story-gallery">
          <article
            v-for="story in sortedStories"
            :key="story.id"
            class="story-card compact-story-card panel gallery-story-card"
            :class="{ active: selectedStory?.story.id === story.id }"
            @click="openStoryReader(story.id)"
          >
            <div class="story-card-top">
              <strong>{{ story.title }}</strong>
              <span class="story-chapter-total">{{ story.chapterCount }} chương</span>
            </div>

            <p class="story-progress-line">{{ storyProgressText(story) }}</p>
            <span class="story-path">{{ story.sourcePath }}</span>

            <div class="story-card-actions">
              <span v-if="story.lastOpenedAt" class="story-time">Mở gần nhất: {{ formatDateTime(story.lastOpenedAt) }}</span>
              <button class="continue-button" @click="continueStory(story.id, $event)">
                {{ storyContinueText(story) }}
              </button>
            </div>
          </article>
        </section>
      </div>

      <div v-if="selectedStory" class="chapter-column panel">
        <div class="column-head">
          <div>
            <p class="eyebrow">Chương</p>
            <h2>{{ selectedStory.story.title }}</h2>
          </div>

          <label class="preset-select">
            <span>Preset reader</span>
            <select v-model="currentPreset">
              <option v-for="preset in presets" :key="preset" :value="preset">{{ preset }}</option>
            </select>
          </label>
        </div>

        <div class="chapter-list">
          <button
            v-for="chapter in selectedStory.chapters"
            :key="chapter.id"
            class="chapter-card"
            :class="{ active: selectedChapterId === chapter.id || realtimeCurrentChapterId === chapter.id }"
            @click="loadChapter(chapter.id, null)"
          >
            <strong>Chương {{ chapter.chapterIndex }}</strong>
            <span>{{ chapter.title }}</span>
          </button>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'reader'" class="workspace reader-workspace">
      <section class="reader-shell">
        <article
          v-if="selectedStory && chapterContent"
          class="reader-column panel centered-reader"
          :class="{ 'edge-read-aloud-mode': useEdgeReadAloud }"
        >
          <div class="reader-layout" :class="{ 'edge-read-aloud-layout': useEdgeReadAloud }">
            <aside v-if="!useEdgeReadAloud" class="premium-player-column">
              <div class="premium-player-card">
                <div class="card-head">
                  <button class="card-head-icon nav-icon" @click="goToSiblingChapter(-1)" :disabled="!chapterAt(-1)">‹</button>
                  <p class="card-head-title">NOW PLAYING</p>
                  <div class="card-head-actions">
                    <button class="card-head-icon tune-trigger" title="Tinh chỉnh">⋮</button>
                    <div class="player-settings-hover">
                      <div class="hover-voice-row">
                        <span class="setting-label">Giọng đọc</span>
                        <select class="hover-voice-select" v-model="selectedVoice" :disabled="realtimeConnecting || realtimeVoiceOptions.length === 0">
                          <option v-for="voice in realtimeVoiceOptions" :key="voice.id" :value="voice.id">
                            {{ voice.friendlyName }}
                          </option>
                        </select>
                      </div>
                      <div class="hover-sliders">
                        <div class="hover-slider-col">
                          <span class="setting-label">Tốc độ</span>
                          <div class="vertical-slider-track">
                            <input class="vertical-range" v-model.number="realtimeSpeed" type="range" min="-50" max="50" step="5" />
                          </div>
                          <strong>{{ realtimeSpeed }}%</strong>
                        </div>
                        <div class="hover-slider-col">
                          <span class="setting-label">Cao độ</span>
                          <div class="vertical-slider-track">
                            <input class="vertical-range" v-model.number="realtimePitch" type="range" min="-80" max="80" step="5" />
                          </div>
                          <strong>{{ realtimePitch }}Hz</strong>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="player-artwork">
                  <div class="artwork-inner">
                    <span class="artwork-emoji">📖</span>
                  </div>
                  <div class="artwork-glow"></div>
                </div>

                <div class="player-info-block">
                  <h3 class="playing-title">{{ realtimeCurrentChapterTitle || chapterContent.chapterTitle }}</h3>
                  <p class="playing-subtitle">{{ chapterContent.storyTitle }}</p>
                </div>

                <div class="player-main-controls">
                  <button class="neume-btn heart-btn" title="Yêu thích">
                    <span class="heart-glyph">❤</span>
                  </button>
                  <button class="neume-btn prev-btn" @click="goToSiblingChapter(-1)" :disabled="!chapterAt(-1)" title="Chương trước">
                    <span class="skip-glyph left"></span>
                  </button>
                  <button class="neume-btn play-pause-btn" @click="togglePlayback" :class="{ 'is-playing': realtimeStatus === 'reading' || edgeReadAloudActive }">
                    <span class="center-glyph" :class="{ 'is-playing': realtimeStatus === 'reading' || edgeReadAloudActive }"></span>
                  </button>
                  <button class="neume-btn next-btn" @click="goToSiblingChapter(1)" :disabled="!chapterAt(1)" title="Chương sau">
                    <span class="skip-glyph right"></span>
                  </button>
                </div>

                <div class="player-progress-section">
                  <div class="progress-bar-container" @click="seekAudio">
                    <div class="progress-filled" :style="{ width: (audioCurrentTime / (audioDuration || 1) * 100) + '%' }"></div>
                    <div class="progress-knob" :style="{ left: (audioCurrentTime / (audioDuration || 1) * 100) + '%' }"></div>
                  </div>
                  <div class="time-labels">
                    <span>{{ formatDuration(audioCurrentTime) }}</span>
                    <span>{{ formatDuration(audioDuration) }}</span>
                  </div>
                </div>

                <div class="lyrics-hint">
                  <span class="lyrics-arrow">⌃</span>
                  <span>LYRICS</span>
                </div>

                <audio
                  ref="audioRef"
                  class="audio-player-hidden"
                  @timeupdate="handleTimeUpdate"
                  @pause="scheduleProgressSave"
                  @play="userPausedAudio = false"
                />
              </div>
            </aside>

            <section class="reader-text-pane" :class="{ 'edge-read-aloud-text-pane': useEdgeReadAloud }">
              <header class="reader-head" :class="{ 'edge-read-aloud-hidden': useEdgeReadAloud }">
                <div>
                  <p class="eyebrow">Đang đọc</p>
                  <h2>{{ chapterContent.chapterTitle }}</h2>
                  <p class="meta">
                    {{ chapterContent.storyTitle }} · chương {{ selectedChapterPosition }} · {{ chapterContent.characterCount }} ký tự ·
                    {{ chapterWordCount }} từ
                  </p>
                </div>

                <div class="reader-actions">
                  <button class="ghost-button" @click="goToSiblingChapter(-1)" :disabled="!chapterAt(-1)">Chương trước</button>
                  <button class="ghost-button" @click="goToSiblingChapter(1)" :disabled="!chapterAt(1)">Chương sau</button>
                </div>
              </header>

              <section ref="readerBody" class="reader-body" tabindex="0" @scroll="scheduleProgressSave">
                <template v-for="(block, index) in formattedChapterBlocks" :key="`${chapterContent.chapterId}-${index}`">
                  <h3 v-if="block.kind === 'heading'" class="reader-heading" :class="{ 'active-reading': showLegacyReadingHighlight && activeReadingBlockIndex === index }">{{ block.text }}</h3>
                  <div v-else-if="block.kind === 'divider'" class="reader-divider" :class="{ 'active-reading': showLegacyReadingHighlight && activeReadingBlockIndex === index }">{{ block.text }}</div>
                  <div v-else-if="block.kind === 'spacer'" class="reader-spacer" aria-hidden="true"></div>
                  <p v-else class="reader-paragraph" :class="{ 'active-reading': showLegacyReadingHighlight && activeReadingBlockIndex === index }">{{ block.text }}</p>
                </template>
              </section>

              <footer v-if="isEdgeBrowser" class="edge-read-aloud-dock" :class="{ active: edgeReadAloudActive }">
                <div class="edge-dock-meta">
                  <label class="edge-read-aloud-toggle">
                    <input v-model="useEdgeReadAloud" type="checkbox" />
                    <span>Dùng Read Aloud của Edge</span>
                  </label>
                  <label class="edge-wpm-control">
                    <span>WPM</span>
                    <input v-model.number="edgeReadAloudWordsPerMinute" type="number" min="120" max="260" step="5" />
                  </label>
                </div>

                <div class="edge-dock-actions">
                  <button class="ghost-button edge-dock-button" @click="activeTab = 'library'">Về thư viện</button>
                  <button class="ghost-button edge-dock-button" @click="goToSiblingChapter(-1)" :disabled="!chapterAt(-1)">Trước</button>
                  <button class="ghost-button edge-dock-button edge-dock-play" @click="togglePlayback" :disabled="!useEdgeReadAloud">
                    {{ edgeReadAloudActive ? 'Pause Edge' : 'Play Edge' }}
                  </button>
                  <button class="ghost-button edge-dock-button" @click="goToSiblingChapter(1)" :disabled="!chapterAt(1)">Sau</button>
                </div>
              </footer>
            </section>
          </div>
        </article>

        <article v-else class="empty-state panel">
          <p class="eyebrow">Bắt đầu</p>
          <h2>Chọn thư mục gốc để tạo thư viện truyện local</h2>
          <p class="lead compact">
            Cấu trúc v1: một thư mục gốc, mỗi thư mục con là một truyện, mỗi file <code>.txt</code> bên trong là một chương.
          </p>
        </article>
      </section>
    </section>
  </main>
</template>

<style scoped>
.hidden-input {
  display: none;
}

.error-banner {
  margin: 0;
  padding: 0.9rem 1.2rem;
  border-radius: var(--radius-md);
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
  border: 1px solid rgba(239, 68, 68, 0.18);
}

.eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--accent);
  font-weight: 700;
}

.app-shell {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1rem 1.25rem 1.25rem;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow: hidden;
}

.app-shell.edge-read-aloud-shell {
  padding-top: 0.5rem;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1.25rem;
  background: var(--bg-panel);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  flex-shrink: 0;
}

.edge-read-aloud-hidden {
  display: none !important;
}

.branding {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.logo-icon {
  font-size: 1.6rem;
  line-height: 1;
}

.app-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.app-subtitle {
  font-size: 0.82rem;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

button {
  background: var(--bg-active);
  color: var(--text-active);
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: var(--radius-sm);
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

button:hover:not(:disabled) {
  background: var(--bg-active-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.ghost-button {
  background: var(--bg-panel);
  color: var(--text-primary);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}

.ghost-button:hover:not(:disabled) {
  background: var(--bg-panel-hover);
  color: var(--accent);
  border-color: var(--accent);
}

.app-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  padding: 0 0.25rem 0.35rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.35rem;
}

.app-tabs button {
  background: rgba(59, 130, 246, 0.06);
  color: var(--text-secondary);
  border: 1px solid transparent;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.42rem 0.72rem;
  box-shadow: none;
  border-radius: 999px;
  cursor: pointer;
  min-height: 0;
}

.app-tabs button:hover:not(:disabled) {
  color: var(--text-primary);
  background: transparent;
  box-shadow: none;
  transform: none;
}

.app-tabs button.active {
  color: var(--accent);
  border-color: rgba(59, 130, 246, 0.25);
  background: rgba(59, 130, 246, 0.12);
}

.workspace {
  gap: 1.5rem;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0 0.5rem 1rem;
}

.library-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  align-items: stretch;
}

.library-main {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.library-summary {
  flex: 0 0 auto;
}

.story-gallery {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
  align-content: start;
  padding-right: 0.25rem;
}

.reader-workspace {
  display: flex;
  justify-content: center;
  min-height: 0;
  overflow: hidden;
}

.reader-shell {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  width: 100%;
  max-width: 1400px;
}

.panel {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.library-main,
.chapter-column {
  min-height: 0;
}

.sidebar-head,
.column-head {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel-hover);
}

.sidebar-head h2,
.column-head h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
}

.library-root {
  padding: 1rem 1.5rem 0;
}

.meta {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.chapter-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.story-card,
.chapter-card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  padding: 1rem;
  border-radius: var(--radius-md);
  text-align: left;
  color: var(--text-primary);
}

.compact-story-card {
  gap: 0.7rem;
  padding: 0.95rem 1rem;
  cursor: pointer;
  min-height: 170px;
  justify-content: space-between;
}

.gallery-story-card {
  overflow: hidden;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.gallery-story-card:hover {
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.28);
}

.story-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.8rem;
}

.story-chapter-total {
  white-space: nowrap;
  font-size: 0.78rem;
  padding: 0.24rem 0.55rem;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.08);
  color: var(--accent);
  font-weight: 700;
}

.story-progress-line {
  margin: 0;
  font-size: 0.88rem;
  color: var(--text-primary);
  font-weight: 600;
}

.story-card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
}

.continue-button {
  padding: 0.5rem 0.8rem;
  font-size: 0.82rem;
  border-radius: 999px;
}

.story-card.active,
.chapter-card.active {
  background: var(--bg-active);
  color: var(--text-active);
  border-color: var(--bg-active);
}

.story-card.active *,
.chapter-card.active * {
  color: var(--text-active) !important;
}

.story-path,
.story-time {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.reader-column {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-panel);
}

.reader-layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(280px, 320px) minmax(0, 1fr);
}

.reader-layout.edge-read-aloud-layout {
  grid-template-columns: minmax(0, 1fr);
}

.reader-text-pane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--border);
}

.reader-text-pane.edge-read-aloud-text-pane {
  border-left: none;
}

.edge-read-aloud-mode .reader-body {
  padding-top: 1rem;
}

.edge-read-aloud-dock {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  padding: 0.9rem 1.1rem;
  border-top: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.22);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.edge-read-aloud-dock.active {
  position: sticky;
  bottom: 0;
  z-index: 5;
  backdrop-filter: blur(8px);
}

.edge-dock-meta {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  flex-wrap: wrap;
}

.edge-dock-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.edge-dock-button {
  min-width: 6.75rem;
}

.edge-dock-play {
  min-width: 7.5rem;
}

.reader-head {
  padding: 1rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel-hover);
  flex-shrink: 0;
}

.reader-head h2 {
  margin: 0 0 0.3rem;
  font-size: 1.15rem;
}

.reader-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.premium-player-column {
  padding: 0.9rem 0.7rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.05) 0%, rgba(15, 23, 42, 0.01) 100%);
}

.premium-player-card {
  width: 100%;
  max-width: 270px;
  margin: 0 auto;
  background: #e9edf4;
  border-radius: 18px;
  padding: 0.75rem 0.65rem 0.8rem;
  box-shadow:
    8px 8px 18px rgba(148, 163, 184, 0.35),
    -8px -8px 18px rgba(255, 255, 255, 0.75);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  position: relative;
  transition: transform 0.25s ease;
}

.premium-player-card:hover {
  transform: translateY(-2px);
}

.card-head {
  width: 100%;
  display: grid;
  grid-template-columns: 22px 1fr 22px;
  align-items: center;
  gap: 0.25rem;
}

.card-head-title {
  margin: 0;
  text-align: center;
  font-size: 0.5rem;
  letter-spacing: 0.08em;
  font-weight: 700;
  color: #334155;
}

.card-head-icon {
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: #475569;
  font-size: 0.9rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  box-shadow: none;
  padding: 0;
}

.card-head-icon:hover:not(:disabled) {
  transform: none;
  background: rgba(148, 163, 184, 0.18);
  box-shadow: none;
}

.card-head-icon:disabled {
  opacity: 0.45;
}

.card-head-actions {
  position: relative;
  justify-self: end;
}

.player-artwork {
  width: 100%;
  max-width: 190px;
  aspect-ratio: 1 / 1;
  border-radius: 10px;
  background:
    radial-gradient(circle at 65% 38%, rgba(59, 130, 246, 0.45), transparent 46%),
    linear-gradient(145deg, #0b1020 0%, #1f2a44 55%, #6b7280 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.08);
}

.artwork-inner {
  font-size: 2.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  filter: drop-shadow(0 2px 5px rgba(15, 23, 42, 0.4));
}

.artwork-glow {
  position: absolute;
  inset: 0;
  background:
    repeating-radial-gradient(circle at 50% 46%, rgba(148, 163, 184, 0.1) 0 2px, transparent 2px 6px);
  opacity: 0.35;
  z-index: 1;
  pointer-events: none;
}

.player-info-block {
  text-align: center;
  min-width: 0;
  width: 100%;
  margin-top: 0.1rem;
}

.playing-title {
  font-size: 1.02rem;
  color: #475569;
  margin: 0 0 0.12rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playing-subtitle {
  font-size: 0.62rem;
  color: #94a3b8;
  margin: 0;
  font-weight: 600;
}

.player-main-controls {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: nowrap;
  margin-top: 0.2rem;
}

.edge-read-aloud-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 0.85rem;
  font-size: 0.72rem;
  color: #64748b;
}

.edge-read-aloud-toggle,
.edge-wpm-control {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.edge-read-aloud-toggle input,
.edge-wpm-control input {
  accent-color: #2563eb;
}

.edge-wpm-control input {
  width: 4.25rem;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  padding: 0.22rem 0.5rem;
  color: #0f172a;
}

.neume-btn {
  border: none !important;
  background: #edf1f7;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow:
    5px 5px 10px rgba(148, 163, 184, 0.35),
    -5px -5px 10px rgba(255, 255, 255, 0.9) !important;
  color: #64748b;
  padding: 0;
}

.neume-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow:
    7px 7px 12px rgba(148, 163, 184, 0.32),
    -6px -6px 12px rgba(255, 255, 255, 0.9) !important;
  background: #f2f5fa;
}

.neume-btn:active {
  box-shadow:
    inset 4px 4px 8px rgba(148, 163, 184, 0.34),
    inset -4px -4px 8px rgba(255, 255, 255, 0.9) !important;
  transform: scale(0.98);
}

.prev-btn,
.next-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  font-size: 0.7rem;
}

.play-pause-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #e7edf5;
  color: #2563eb;
}

.heart-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
}

.heart-glyph {
  font-size: 0.74rem;
  color: #f43f5e;
  line-height: 1;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.75);
}

.skip-glyph {
  position: relative;
  display: block;
  width: 12px;
  height: 10px;
  border-left: 1.6px solid #9aa7ba;
}

.skip-glyph::before,
.skip-glyph::after {
  content: '';
  position: absolute;
  top: 1px;
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-right: 4px solid #9aa7ba;
}

.skip-glyph::before {
  left: 1px;
}

.skip-glyph::after {
  left: 5px;
}

.skip-glyph.right {
  transform: scaleX(-1);
}

.center-glyph {
  position: relative;
  display: block;
  width: 0;
  height: 0;
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
  border-left: 10px solid #0284c7;
  margin-left: 2px;
}

.center-glyph.is-playing {
  width: 14px;
  height: 14px;
  margin-left: 0;
  border: none;
  border-radius: 3px;
  background: #0284c7;
  box-shadow: inset 0 0 0 1px #0369a1;
}

.center-glyph.is-playing::before,
.center-glyph.is-playing::after {
  content: '';
  position: absolute;
  top: 3px;
  width: 2px;
  height: 8px;
  background: #ffffff;
  border-radius: 1px;
}

.center-glyph.is-playing::before {
  left: 4px;
}

.center-glyph.is-playing::after {
  left: 8px;
}

.player-progress-section {
  width: 86%;
  margin-top: 0.05rem;
}

.progress-bar-container {
  height: 4px;
  background: #d5dde8;
  border-radius: 100px;
  position: relative;
  cursor: pointer;
  overflow: hidden;
}

.progress-filled {
  height: 100%;
  background: #7f8fa7;
  border-radius: 100px;
  width: 0%;
  transition: width 0.1s linear;
}

.progress-bar-container:hover .progress-filled {
  background: #64748b;
}

.progress-knob {
  display: none; /* Hide knob for a cleaner look like the image */
}

.time-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.35rem;
  font-size: 0.52rem;
  color: #9aa7ba;
  font-weight: 700;
}

.setting-label {
  font-size: 0.56rem !important;
  text-transform: uppercase;
  color: #64748b;
  font-weight: 800;
}

.tune-trigger {
  font-size: 0.86rem;
  font-weight: 700;
}

.player-settings-hover {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  width: 190px;
  padding: 0.5rem;
  border-radius: 12px;
  background: #f2f6fb;
  border: 1px solid rgba(148, 163, 184, 0.24);
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.2);
  opacity: 0;
  pointer-events: none;
  transform: translateY(6px) scale(0.98);
  transition: opacity 0.18s ease, transform 0.18s ease;
  z-index: 10;
}

.card-head-actions:hover .player-settings-hover,
.card-head-actions:focus-within .player-settings-hover {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0) scale(1);
}

.hover-voice-row {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 0.5rem;
}

.hover-voice-select {
  width: 100%;
  font-size: 0.68rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 8px;
  padding: 0.26rem 0.4rem;
  background: white;
  color: #0f172a;
}

.hover-sliders {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.45rem;
}

.hover-slider-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.vertical-slider-track {
  width: 28px;
  height: 74px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vertical-range {
  width: 74px;
  margin: 0;
  transform: rotate(-90deg);
  accent-color: #2563eb;
}

.hover-slider-col strong {
  font-size: 0.58rem;
  color: #334155;
  font-weight: 700;
}

.lyrics-hint {
  margin-top: 0.2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.08rem;
  color: #94a3b8;
  font-size: 0.5rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.lyrics-arrow {
  font-size: 0.48rem;
  line-height: 1;
}

.audio-player-hidden {
  display: none;
}

.reader-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 1.8rem 2rem;
  font-family: var(--font-serif);
  font-size: 1.08rem;
  line-height: 1.9;
  scroll-behavior: smooth;
}

.reader-heading {
  margin: 0 0 1rem;
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 1.08rem;
  font-weight: 700;
  white-space: pre-wrap;
}

.reader-paragraph {
  margin: 0;
  color: var(--text-primary);
  white-space: pre-wrap;
  line-height: 1.9;
}

.reader-divider {
  margin: 0;
  color: var(--text-muted);
  white-space: pre-wrap;
  letter-spacing: 0.04em;
}

.reader-spacer {
  height: 1.1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 4rem;
}

.compact {
  max-width: 500px;
}

.preset-select {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.preset-select span {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preset-select select {
  padding: 0.6rem 1rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-primary);
  outline: none;
  font-weight: 500;
  color: var(--text-primary);
}

.recent-strip {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 1.5rem 0;
  flex-wrap: wrap;
}

.recent-chip {
  padding: 0.4rem 0.8rem;
  background: rgba(59, 130, 246, 0.1);
  color: var(--accent);
  border-radius: 99px;
  font-size: 0.85rem;
  font-weight: 600;
}

@media (max-width: 1200px) {
  .app-shell {
    height: auto;
    overflow: visible;
    min-height: 100vh;
  }

  .workspace {
    display: flex;
    flex-direction: column;
    overflow: visible;
  }

  .reader-shell {
    max-width: 100%;
  }

  .library-main,
  .chapter-column {
    height: auto;
    flex: none;
  }

  .story-gallery {
    overflow: visible;
    grid-template-columns: 1fr;
    padding-right: 0;
  }

  .reader-layout {
    grid-template-columns: 1fr;
  }

  .premium-player-column {
    border-bottom: 1px solid var(--border);
  }

  .reader-text-pane {
    border-left: none;
  }

  .reader-body {
    padding: 1.25rem;
  }

  .app-header,
  .reader-head {
    flex-direction: column;
    align-items: stretch;
  }

  .reader-actions {
    width: 100%;
  }

  .reader-actions .ghost-button {
    flex: 1;
  }

  .player-main-controls {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .edge-read-aloud-dock {
    align-items: stretch;
    flex-direction: column;
  }

  .edge-dock-actions {
    width: 100%;
  }

  .edge-dock-button {
    flex: 1;
  }
}
</style>

