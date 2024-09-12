# charm-vantage-agent

# Usage

Follow the steps below to get started.

### Build the charm

Running the following command will produce a .charm file, `vantage-agent.charm`

```bash
charmcraft build
```

### Create the vantage-agent charm config

`vantage-agent.yaml`

```yaml
vantage-agent:
  base-api-url: "<base-api-url>"
  oidc-domain: "<oidc-domain>"
  oidc-client-id: "<oidc-client-id>"
  oidc-client-secret: "<oidc-client-secret>"
```

e.g.

```yaml
vantage-agent:
  base-api-url: "https://apis.vantagehpc.io/cluster"
  oidc-domain: "auth.vantagehpc.io"
  oidc-client-id: "ae4e7c40-7889-45ae-bd36-1ad2f25dc679"
  oidc-client-secret: "LMmPxusATyKz_dp63hjeJO7cFUayiYvudGv4r3gUk_4"
```

### Deploy the charm

Using the built charm and the defined config, run the command to deploy the charm.

```bash
juju deploy ./vantage-agent.charm \
    --config ./vantage-agent.yaml \
    --series jammy
```

### Charm Actions

The vantage-agent charm exposes additional functionality to facilitate vantage-agent
package upgrades.

To upgrade the vantage-agent to a new version or release:

```bash
juju run-action vantage-agent/leader upgrade version="7.7.7"
```

This will result in the vantage-agent package upgrade to 7.7.7.

Manually triggers the cleaning of vantage-agent's cache dir:

```bash
juju run-action vantage-agent/leader clear-cache-dir
```

#### License

* MIT (see `LICENSE` file in this directory for full preamble)