## Tableau des mesures DOS1102 – CH1

Ce tableau est basé sur un scan réalisé avec :

```bash
python -m tools.dos1102_cli --scan-meas
```

Statut :
- **OK** : une réponse texte a été reçue.
- **Aucune réponse** : timeout USB (aucune donnée reçue).

| Commande                 | Statut          | Aperçu réponse    |
|--------------------------|----------------|-------------------|
| `:MEAS:CH1:PERiod?`      | OK             | `T : 100.000us`   |
| `:MEAS:CH1:FREQuency?`   | OK             | `F : 10.00kHz`    |
| `:MEAS:CH1:AVERage?`     | OK             | `V : -110.1mV`    |
| `:MEAS:CH1:PKPK?`        | OK             | `Vpp : 5.156V`    |
| `:MEAS:CH1:SQUARESUM?`   | Aucune réponse |                   |
| `:MEAS:CH1:MAX?`         | OK             | `Ma : 2.500V`     |
| `:MEAS:CH1:MIN?`         | OK             | `Mi : -2.578V`    |
| `:MEAS:CH1:VTOP?`        | OK             | `Vt : 2.500V`     |
| `:MEAS:CH1:VBASe?`       | OK             | `Vb : -2.578V`    |
| `:MEAS:CH1:VAMP?`        | OK             | `Va : 5.078V`     |
| `:MEAS:CH1:VPRESHOOT?`   | Aucune réponse |                   |
| `:MEAS:CH1:PREShoot?`    | OK             | `Ps : 1.6%`       |
| `:MEAS:CH1:RTime?`       | OK             | `RT : 29.000us`   |
| `:MEAS:CH1:FTime?`       | OK             | `FT : 30.000us`   |
| `:MEAS:CH1:PWIDth?`      | OK             | `PW : 50.000us`   |
| `:MEAS:CH1:NWIDth?`      | OK             | `NW : 50.000us`   |
| `:MEAS:CH1:PDUTy?`       | OK             | `+D : 50.0%`      |
| `:MEAS:CH1:NDUTy?`       | OK             | `-D : 50.0%`      |
| `:MEAS:CH1:RDELay?`      | OK             | `PD : 99.000us`   |
| `:MEAS:CH1:FDELay?`      | OK             | `ND : 0.000ns`    |
| `:MEAS:CH1:TRUERMS?`     | Aucune réponse |                   |
| `:MEAS:CH1:CYCRms?`      | OK             | `TR : 1.801V`     |
| `:MEAS:CH1:WORKPERIOD?`  | Aucune réponse |                   |
| `:MEAS:CH1:RISEPHASEDELAY?` | OK          | `RP : 0.000°`     |
| `:MEAS:CH1:PPULSENUM?`   | Aucune réponse |                   |
| `:MEAS:CH1:NPULSENUM?`   | Aucune réponse |                   |
| `:MEAS:CH1:RISINGEDGENUM?`  | Aucune réponse |                |
| `:MEAS:CH1:FALLINGEDGENUM?` | Aucune réponse |                |
| `:MEAS:CH1:AREA?`        | Aucune réponse |                   |

