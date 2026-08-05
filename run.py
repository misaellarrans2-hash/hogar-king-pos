from app import create_app

app = create_app()

if __name__ == "__main__":
    # host 0.0.0.0 para poder abrir el sistema tambien desde un celular
    # conectado a la misma red WiFi (util para el bodeguero mas adelante).
    app.run(host="0.0.0.0", port=5000, debug=True)
