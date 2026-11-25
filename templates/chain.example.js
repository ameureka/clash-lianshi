const MAIN_GROUP_NAME = "主代理组";
const EXIT_NAME = "美国出口-SOCKS5";
const FRONT_GROUP_NAME = "前置选择";

function main(config, profileName) {
  if (!config || !Array.isArray(config["proxy-groups"])) {
    throw new Error("Missing subscription proxy groups");
  }
  const matches = config["proxy-groups"].filter(group =>
    group && group.name === MAIN_GROUP_NAME &&
    ["select", "selector"].includes(group.type)
  );
  if (matches.length !== 1) {
    throw new Error("Set MAIN_GROUP_NAME to one existing selection group");
  }
  const group = matches[0];
  if (!Array.isArray(group.proxies)) {
    throw new Error("The main group must have an inline proxies array");
  }
  group.proxies = [EXIT_NAME, FRONT_GROUP_NAME, ...group.proxies.filter(name =>
    name !== EXIT_NAME && name !== FRONT_GROUP_NAME
  )];
  group["default-selected"] = EXIT_NAME;
  return config;
}
