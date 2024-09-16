module.exports = {
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://localhost:8000/api/:path*', // FastAPIが動作しているURLに変更
            },
        ];
    },
};