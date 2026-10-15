// Open the app with ?demo to preview the results screen without a backend.
export const mockResult = {
  mediaUrl: null,
  chapters: [
    { index: 0, start: 0, end: 95, title: 'Welcome and guest background', keywords: ['guest', 'career', 'startup'], sentiment: { label: 'positive', compound: 0.62 }, is_micro: false },
    { index: 1, start: 95, end: 410, title: 'How remote work changed hiring', keywords: ['remote', 'hiring', 'culture'], sentiment: { label: 'neutral', compound: 0.02 }, is_micro: false },
    { index: 2, start: 410, end: 640, title: 'Tooling and async communication', keywords: ['async', 'meetings', 'documentation'], sentiment: { label: 'positive', compound: 0.31 }, is_micro: false },
    { index: 3, start: 640, end: 900, title: 'Burnout and setting boundaries', keywords: ['burnout', 'boundaries', 'schedule'], sentiment: { label: 'negative', compound: -0.28 }, is_micro: false },
  ],
  transcript: [
    { start: 0, end: 6, text: "Welcome back to the show, today we're joined by someone who built a fully remote company." },
    { start: 6, end: 14, text: 'Before we dive in, tell us how you ended up founding a startup in the first place.' },
    { start: 95, end: 104, text: "So let's talk about how remote work has changed the way teams hire." },
    { start: 104, end: 115, text: "We stopped caring where people live, and that widened our candidate pool enormously." },
    { start: 410, end: 421, text: "The biggest shift was writing things down instead of calling a meeting for everything." },
    { start: 640, end: 652, text: "The risk is that work never stops, so you have to make sure you protect your evenings." },
  ],
  notes: {
    summary:
      'The guest explains how running a fully remote company widened hiring, pushed the team toward written, asynchronous communication, and made burnout a real risk that needs explicit boundaries.',
    topics: ['remote work', 'hiring', 'async communication', 'burnout'],
    key_points: [
      { chapter_index: 0, start: 0, title: 'Welcome and guest background', summary: 'Introduces the guest and how they came to found a remote-first startup.', points: ['Guest built a fully remote company from day one.'], sentiment: { label: 'positive', compound: 0.62 } },
      { chapter_index: 1, start: 95, title: 'How remote work changed hiring', summary: 'Remote hiring removed location limits and widened the candidate pool.', points: ['Location stopped being a hiring filter.', 'Candidate pool grew enormously.'], sentiment: { label: 'neutral', compound: 0.02 } },
      { chapter_index: 2, start: 410, title: 'Tooling and async communication', summary: 'Writing replaced many meetings.', points: ['Default to writing things down before scheduling a call.'], sentiment: { label: 'positive', compound: 0.31 } },
      { chapter_index: 3, start: 640, title: 'Burnout and setting boundaries', summary: 'Work can bleed into evenings without clear limits.', points: ['Protect evenings explicitly.'], sentiment: { label: 'negative', compound: -0.28 } },
    ],
    action_items: [
      { start: 410, text: 'Write things down instead of calling a meeting for everything.' },
      { start: 640, text: 'Make sure you protect your evenings.' },
    ],
  },
}
