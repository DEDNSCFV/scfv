# SCFV – Núcleo Operativo v1.0

**Sistema Contable Formalmente Verificado**  
Autor: Domingo E. Díaz N. (C.P.C. Nº 183594)

---

## Propósito

El SCFV es un sistema contable local‑first diseñado para contadores públicos. Este núcleo operativo cubre los módulos esenciales:

- **Diario, Mayor, Inventario, Fiscal, Balance General**
- **Multimoneda** (VES, USD, EUR, CNY, TRY, RUB)
- **Inflación (NIC 29)** con factores históricos y manuales
- **Auditoría criptográfica** con hash chain
- **CLI profesional** (Termux / Linux / macOS)

---

## Instalación

```bash
tar -xzvf SCFV_Nucleo_Operativo_v1.0.tar.gz
cd scfv
bash INSTALAR.sh
./scfv --version   # Debe mostrar "SCFV v1.0"
./scfv salud       # Verifica integridad del sistema
