// web/html/js/webrtc-client.js
class WebRTCFileShare {
    constructor(signalingUrl = 'http://localhost:5001') {
        this.socket = io(signalingUrl);
        this.peerConnection = null;
        this.dataChannel = null;
        this.roomId = null;
        this.selectedFile = null;
        this.isDataChannelReady = false;

        this.pageRole = document.getElementById('pageRole')?.value || 'unknown';
        console.log('Page role:', this.pageRole);

        this.setupSocketListeners();
        this.updateUI('ready', 'Подключение к серверу...');
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to signaling server');
            this.updateUI('connected', 'Подключено к серверу');
        });

        this.socket.on('room_created', (data) => {
            this.roomId = data.roomId;
            console.log('Room created:', this.roomId);

            // Показываем информацию о комнате
            document.getElementById('roomIdDisplay').textContent = this.roomId;
            const shareUrl = `${window.location.origin}/receive.html?room=${this.roomId}`;
            document.getElementById('shareLink').value = shareUrl;
            document.getElementById('roomInfo').style.display = 'block';

            this.createPeerConnection(true);
            this.updateUI('room_created', 'Комната создана, ожидание получателя...');
        });

        this.socket.on('peer_connected', () => {
            console.log('Peer connected, creating offer');
            this.updateUI('peer_connected', 'Получатель подключился! Выберите файл.');
            document.getElementById('fileSection').style.display = 'block';
            this.createOffer();
        });

        this.socket.on('offer', async (offer) => {
            console.log('Received offer');
            this.updateUI('receiving', 'Получен запрос на соединение...');
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
            const answer = await this.peerConnection.createAnswer();
            await this.peerConnection.setLocalDescription(answer);
            this.socket.emit('answer', { room: this.roomId, answer });
        });

        this.socket.on('answer', async (answer) => {
            console.log('Received answer');
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
            this.updateUI('connected', 'Соединение установлено!');
        });

        this.socket.on('ice_candidate', (candidate) => {
            console.log('Received ICE candidate');
            this.peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
        });

        this.socket.on('disconnect', () => {
            this.updateUI('disconnected', 'Потеряно соединение с сервером');
        });

        // Новый обработчик ошибок
        this.socket.on('error', (data) => {
            console.error('Server error:', data.message);
            alert(`Ошибка: ${data.message}`);
            this.updateUI('error', `Ошибка: ${data.message}`);
        });

        // Обработчик отключения получателя
        this.socket.on('receiver_disconnected', () => {
            console.log('Receiver disconnected');
            this.updateUI('receiver_left', 'Получатель отключился');
            if (this.pageRole === 'sender') {
                document.getElementById('fileSection').style.display = 'none';
                document.getElementById('sendBtn').disabled = true;
            }
        });

        // Обработчик отключения отправителя
        this.socket.on('sender_disconnected', () => {
            console.log('Sender disconnected');
            this.updateUI('sender_left', 'Отправитель отключился');
            if (this.pageRole === 'receiver') {
                document.getElementById('status').textContent = 'Отправитель отключился';
            }
        });
    }

    createPeerConnection(isSender) {
        console.log('Creating peer connection, isSender:', isSender);

        const config = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };

        this.peerConnection = new RTCPeerConnection(config);

        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.emit('ice_candidate', {
                    room: this.roomId,
                    candidate: event.candidate
                });
            }
        };

        this.peerConnection.oniceconnectionstatechange = () => {
            console.log('ICE state:', this.peerConnection.iceConnectionState);
        };

        if (isSender) {
            this.dataChannel = this.peerConnection.createDataChannel('fileTransfer');
            this.setupDataChannel();
        } else {
            this.peerConnection.ondatachannel = (event) => {
                this.dataChannel = event.channel;
                this.setupDataChannel();
            };
        }

        if (isSender) {
            console.log('Creating data channel as sender');
            this.dataChannel = this.peerConnection.createDataChannel('fileTransfer');
            this.setupDataChannel();
        } else {
            console.log('Waiting for data channel as receiver');
            this.peerConnection.ondatachannel = (event) => {
                console.log('Data channel received from sender');
                this.dataChannel = event.channel;
                this.setupDataChannel();
            };
        }

    }

    setupDataChannel() {
        this.dataChannel.onopen = () => {
            console.log('DataChannel open');
            this.isDataChannelReady = true;
            this.updateUI('datachannel_open', 'Канал передачи открыт');

            // Активируем кнопку отправки если файл выбран
            const sendBtn = document.getElementById('sendBtn');
            if (sendBtn && this.selectedFile) {
                sendBtn.disabled = false;
            }
        };

        this.dataChannel.onclose = () => {
            console.log('DataChannel closed');
            this.isDataChannelReady = false;
            this.updateUI('datachannel_closed', 'Канал передачи закрыт');
        };

        this.dataChannel.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'metadata') {
                // Получаем информацию о файле
                this.fileMetadata = {
                    name: data.name,
                    size: data.size,
                    chunks: data.chunks,
                    receivedChunks: new Array(data.chunks)
                };

                // Показываем прогресс
                const progressDiv = document.querySelector('.progress');
                const progressBar = document.getElementById('progressBar');
                progressDiv.style.display = 'block';

                // ОБНОВЛЕНО: показываем название файла в статусе
                document.getElementById('status').innerHTML = `
                    <strong>Файл:</strong> ${data.name}<br>
                    <strong>Размер:</strong> ${(data.size/1024/1024).toFixed(2)} MB<br>
                    <strong>Статус:</strong> Получение...
                `;

            } else if (data.type === 'chunk') {
                // Сохраняем чанк
                this.fileMetadata.receivedChunks[data.index] = data.data;

                // Обновляем прогресс
                const percent = Math.round(((data.index + 1) / data.total) * 100);
                const progressBar = document.getElementById('progressBar');
                progressBar.style.width = percent + '%';
                progressBar.textContent = percent + '%';

                // Если получили все чанки
                if (data.index === data.total - 1) {
                    this.assembleFile();
                }
            }
        };
    }

    createOffer() {
        this.peerConnection.createOffer()
            .then(offer => this.peerConnection.setLocalDescription(offer))
            .then(() => {
                this.socket.emit('offer', {
                    room: this.roomId,
                    offer: this.peerConnection.localDescription
                });
            });
    }

    createRoom() {
        this.socket.emit('create_room');
    }

    joinRoom(roomId) {
        this.roomId = roomId;
        this.socket.emit('join_room', { roomId });
        this.createPeerConnection(false);
        this.updateUI('joining', `Подключение к комнате ${roomId}...`);
    }

    updateUI(state, message) {
        // Для страницы получателя
        const statusDiv = document.getElementById('status');
        const connState = document.getElementById('connectionState');

        if (statusDiv) {
            statusDiv.textContent = message;
            statusDiv.className = 'alert alert-' +
                (state === 'connected' || state === 'datachannel_open' ? 'success' :
                 state === 'disconnected' ? 'danger' : 'info');
        }

        if (connState) {
            connState.textContent = `DataChannel: ${this.isDataChannelReady ? '✅ готов' : '⏳ ожидание'}`;
        }
    }

    sendFile(file) {
        // Подробная диагностика
        console.log('SendFile called');
        console.log('isDataChannelReady flag:', this.isDataChannelReady);
        console.log('SendFile called');
        console.log('DataChannel exists:', this.dataChannel);
        console.log('DataChannel state:', this.dataChannel?.readyState);
        console.log('isDataChannelReady flag:', this.isDataChannelReady);

        if (!this.dataChannel) {
            // Проверяем, не пытается ли получатель отправить файл
            if (document.querySelector('.card-header.bg-success')) {
                alert('Ошибка: Вы находитесь на странице получателя. Отправлять файл нужно на странице отправителя!');
            } else {
                alert('Канал передачи не создан! Подождите установки соединения.');
            }
            return;
        }

        if (this.dataChannel.readyState !== 'open') {
            alert(`Канал передачи в состоянии: ${this.dataChannel.readyState}. Ожидайте...`);
            return;
        }

        if (!this.isDataChannelReady) {
            alert('Канал еще не готов к передаче');
            return;
        }

        // Если дошли сюда - канал открыт и готов
        this.startFileTransfer(file);
    }

    // Выносим логику передачи в отдельный метод
    startFileTransfer(file) {
        const CHUNK_SIZE = 16384; // 16KB
        let offset = 0;
        let chunkIndex = 0;
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

        // Показываем прогресс
        const progressDiv = document.querySelector('.progress');
        const progressBar = document.getElementById('progressBar');
        progressDiv.style.display = 'block';

        // Отправляем метаданные файла
        const metadata = {
            type: 'metadata',
            name: file.name,
            size: file.size,
            chunks: totalChunks
        };
        this.dataChannel.send(JSON.stringify(metadata));

        // Функция чтения и отправки следующего чанка
        const readNextChunk = () => {
            const chunk = file.slice(offset, offset + CHUNK_SIZE);
            const reader = new FileReader();

            reader.onload = (e) => {
                const chunkData = {
                    type: 'chunk',
                    index: chunkIndex,
                    total: totalChunks,
                    data: e.target.result
                };

                this.dataChannel.send(JSON.stringify(chunkData));

                offset += CHUNK_SIZE;
                chunkIndex++;

                // Обновляем прогресс
                const percent = Math.round((chunkIndex / totalChunks) * 100);
                progressBar.style.width = percent + '%';
                progressBar.textContent = percent + '%';

                if (offset < file.size) {
                    readNextChunk();
                } else {
                    progressBar.classList.remove('progress-bar-animated');
                    progressBar.textContent = 'Отправлено!';
                    setTimeout(() => progressDiv.style.display = 'none', 2000);
                }
            };

            reader.readAsArrayBuffer(chunk);
        };

        readNextChunk();
    }

    assembleFile() {
        // Собираем все чанки в Blob
        const chunks = this.fileMetadata.receivedChunks;
        const blob = new Blob(chunks, { type: 'application/octet-stream' });

        // Создаем ссылку для скачивания
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.fileMetadata.name;

        // Показываем кнопку скачивания
        document.getElementById('downloadBtn').onclick = () => a.click();
        document.getElementById('downloadSection').style.display = 'block';

        // Обновляем статус
        const progressBar = document.getElementById('progressBar');
        progressBar.classList.remove('progress-bar-animated');
        document.getElementById('status').innerHTML = `
            <strong>Файл:</strong> ${this.fileMetadata.name}<br>
            <strong>Размер:</strong> ${(this.fileMetadata.size/1024/1024).toFixed(2)} MB<br>
            <strong>Статус:</strong> ✅ Получен! Нажмите кнопку для скачивания
        `;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.client = new WebRTCFileShare();

    // Обработчик выбора файла (для страницы отправки)
    const fileInput = document.getElementById('fileInput');
    const sendBtn = document.getElementById('sendBtn');

    if (fileInput && sendBtn) {
        fileInput.addEventListener('change', (e) => {
            window.client.selectedFile = e.target.files[0];
            if (window.client.selectedFile) {
                document.getElementById('fileInfo').innerHTML = `
                    <strong>Файл:</strong> ${window.client.selectedFile.name}<br>
                    <strong>Размер:</strong> ${(window.client.selectedFile.size / 1024 / 1024).toFixed(2)} MB
                `;
                sendBtn.disabled = false;
            }
        });

        sendBtn.addEventListener('click', () => {
            window.client.sendFile(window.client.selectedFile);
        });
    }
});