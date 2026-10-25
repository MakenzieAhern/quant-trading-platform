import { useTranslation } from "react-i18next";
const en = {
  title: "Named configuration versions",
  changed:
    "The recovery copy changed after this preview opened. No restore was performed. Close this preview, refresh the saved drafts, and review the new values before confirming.",
  recoveries: "Browser page recovery drafts",
  recoveryHelp:
    "Each opened page keeps its latest draft before updating the shared draft. These are recovery copies, not a history of every edit. Another tab may have replaced the shared draft; its copy is retained. A page's copy is cleared only after its experiment is confirmed saved on the server. Restoring a copy does not itself run an experiment. Remaining copies count toward browser storage limits.",
  recover: "Review recovery draft",
  recoveryEmpty: "No browser page recovery drafts are stored.",
  unreadableCopies: "Unreadable draft copies",
  unreadableCopyHelp:
    "Exact original text kept before starting a new draft. Select and copy it for manual recovery. These copies cannot be restored or run here.",
  unreadableCopyEmpty: "No unreadable draft copies are stored.",
  unreadableCopy: "Raw draft copy",
  unreadableRaw: "Original draft text",
  localOnly:
    "Saved only in this browser on this device, not backed up to the server. Clearing browser data can remove these versions. Submitted experiment configurations remain unchanged on the server.",
  name: "Version name",
  save: "Save named version",
  saved: "Configuration version saved in this browser.",
  restore: "Review and restore",
  confirm: "Back up current draft and restore",
  cancel: "Keep current draft",
  restoreHelp:
    "Your current draft will first be kept as a separate backup version. The selected configuration then opens at step 1 with a new request identity. This does not run an experiment or change an existing result.",
  restored:
    "Version restored at step 1. Your previous draft is preserved as a backup. Review all steps before running.",
  backup: "Draft backup before restore",
  backupKind: "Automatic pre-restore backup",
  savedKind: "Named snapshot",
  empty:
    "No named versions yet. Save the current configuration to revisit it later.",
  failed:
    "The version action could not be saved. Your current form and draft have not been replaced. Browser storage may be blocked or full; check it and retry.",
  readFailed:
    "Browser storage could not be read. No empty-library claim or restore is safe until storage is available.",
  corrupt:
    "Some saved records could not be read. They have been retained unchanged, not deleted or overwritten.",
  conflict:
    "The draft changed in another tab. No restore was performed. Save or review both drafts before trying again.",
  retry: "Refresh saved versions",
  created: "Saved at",
  configuration: "Saved configuration",
  exact: "Exact configuration and draft metadata",
  incomplete:
    "Saved values may be unfinished or refer to an unavailable source. Restoring never bypasses the wizard or server validation.",
  restoreTitle: "Restore this saved configuration?",
  count: "Saved versions",
  readonly: "Versions are immutable; saving again creates a new snapshot.",
};
const zh: typeof en = {
  title: "命名配置版本",
  changed:
    "打开预览后，此恢复副本已改变，本次未恢复。请关闭预览，刷新保存草稿并核对新值后再确认。",
  recoveries: "浏览器页面草稿恢复",
  recoveryHelp:
    "每个打开的页面在更新共享草稿前，先保留自己的最新草稿。这是恢复副本，不是每次修改的完整历史。其他标签替换共享草稿后，其副本仍会保留。仅在确认实验已保存到服务端后，才清除该页面的副本。恢复副本本身不会运行实验；其余副本仍会占用浏览器存储空间。",
  recover: "查看恢复草稿",
  recoveryEmpty: "尚无浏览器页面恢复草稿。",
  unreadableCopies: "无法读取的草稿副本",
  unreadableCopyHelp:
    "新建草稿前保留的原始文本。可选中复制以手动恢复；此处不能将副本直接恢复或运行。",
  unreadableCopyEmpty: "尚无无法读取的草稿副本。",
  unreadableCopy: "原始草稿副本",
  unreadableRaw: "原始草稿文本",
  localOnly:
    "仅保存在当前设备的此浏览器中，未备份到服务器。清理浏览器数据可能删除这些版本。已提交实验的服务器配置保持不变。",
  name: "版本名称",
  save: "保存命名版本",
  saved: "配置版本已保存在此浏览器中。",
  restore: "查看并恢复",
  confirm: "备份当前草稿并恢复",
  cancel: "保留当前草稿",
  restoreHelp:
    "先将当前草稿保留为独立备份版本，再把所选配置恢复到第 1 步并生成新请求标识。此操作不会运行实验或修改已有结果。",
  restored: "已恢复到第 1 步，之前的草稿已保留为备份。运行前请逐步核对配置。",
  backup: "恢复前的草稿备份",
  backupKind: "自动恢复前备份",
  savedKind: "命名快照",
  empty: "尚无命名版本，可保存当前配置供以后使用。",
  failed:
    "未能保存版本操作，当前表单及草稿未被替换。浏览器存储可能被阻止或已满，请检查后重试。",
  readFailed:
    "无法读取浏览器存储。存储恢复前，不能认定版本库为空或安全执行恢复。",
  corrupt: "部分保存记录无法读取；已原样保留，未删除或覆盖。",
  conflict:
    "草稿已在另一标签页改变，本次未恢复。请先保存或核对两份草稿后再试。",
  retry: "刷新已保存版本",
  created: "保存时间",
  configuration: "已保存配置",
  exact: "精确配置与草稿元数据",
  incomplete:
    "保存值可能尚未填写完整，或引用当前不可用的来源。恢复不会绕过向导与服务器校验。",
  restoreTitle: "恢复此保存配置？",
  count: "已保存版本数",
  readonly: "版本不可修改；再次保存会创建新快照。",
};
export function useConfigurationCopy() {
  const { i18n } = useTranslation();
  return i18n.language.startsWith("zh") ? zh : en;
}
