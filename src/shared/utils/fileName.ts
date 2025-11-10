export function splitNameExt(name: string) {
  const lastDot = name.lastIndexOf('.');
  if (lastDot <= 0) return { base: name, ext: '' };
  return { base: name.slice(0, lastDot), ext: name.slice(lastDot) };
}

export function buildName(base: string, ext: string) {
  return `${base}${ext}`;
}

export function ensureUniqueName(desired: string, existingNames: Set<string>) {
  if (!existingNames.has(desired)) return desired;
  const { base, ext } = splitNameExt(desired);
  let i = 2;
  while (existingNames.has(buildName(`${base} (${i})`, ext))) i++;
  return buildName(`${base} (${i})`, ext);
}
