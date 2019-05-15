#include "chart.h"
#include <QtGui/QResizeEvent>
#include <QtWidgets/QGraphicsScene>
#include <QtCharts/QChart>
#include <QtCharts/QLineSeries>
#include <QtCharts/QSplineSeries>
#include <QtWidgets/QGraphicsTextItem>


Chart::Chart(QWidget *parent) : QGraphicsView(new QGraphicsScene, parent),
      m_coordX(0), m_coordY(0), m_chart(0)
{
    QVBoxLayout *layout = new QVBoxLayout();
    parent->setLayout(layout);
    layout->addWidget(this);
    QGroupBox *m_legend = new QGroupBox("Series");
    m_groupBox = new QHBoxLayout();
    m_legend->setLayout(m_groupBox);
    layout->addWidget(m_legend);

    setDragMode(QGraphicsView::NoDrag);
    setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    
    // chart
    m_chart = new QChart;
    m_chart->setMinimumSize(640, 480);
    m_chart->legend();

    setRenderHint(QPainter::Antialiasing);
    scene()->addItem(m_chart);

    m_coordX = new QGraphicsSimpleTextItem(m_chart);
    m_coordX->setPos(m_chart->size().width()/2 - 50, m_chart->size().height());
    m_coordX->setText("X: ");
    m_coordY = new QGraphicsSimpleTextItem(m_chart);
    m_coordY->setPos(m_chart->size().width()/2 + 50, m_chart->size().height());
    m_coordY->setText("Y: ");


    this->setMouseTracking(true);

}


void Chart::loadData()
{
//load x axis

//load vertical series
    QSplineSeries *series = new QSplineSeries;
    series->setName("serie1");
    series->append(1.6, 1.4);
    series->append(2.4, 3.5);
    series->append(3.7, 2.5);
    series->append(7, 4);
    series->append(10, 2);
    m_chart->addSeries(series);
    connect(series, &QLineSeries::clicked, this, &Chart::keepCallout);
    connect(series, &QLineSeries::hovered, this, &Chart::tooltip);
    QCheckBox *s_check = new QCheckBox("serie1");
    s_check->setChecked(true);
    m_groupBox->addWidget(s_check);
    connect(s_check, &QCheckBox::toggled, series, &QSplineSeries::setVisible);

    QSplineSeries *series2 = new QSplineSeries;
    series2->setName("serie2");
    series2->append(.6, 1.4);
    series2->append(.4, 3.5);
    series2->append(.7, 2.5);
    series2->append(1, 4);
    series2->append(10, 2);
    m_chart->addSeries(series2);
    connect(series2, &QLineSeries::clicked, this, &Chart::keepCallout);
    connect(series2, &QLineSeries::hovered, this, &Chart::tooltip);
    QCheckBox *s_check2 = new QCheckBox("serie2");
    s_check2->setChecked(true);
    m_groupBox->addWidget(s_check2);
    connect(s_check2, &QCheckBox::toggled, series2, &QSplineSeries::setVisible);

    

    m_chart->createDefaultAxes();
    m_chart->setAcceptHoverEvents(true);
}

void Chart::resizeEvent(QResizeEvent *event)
{
    if (scene()) {
        scene()->setSceneRect(QRect(QPoint(0, 0), event->size()));
         m_chart->resize(event->size());
         m_coordX->setPos(m_chart->size().width()/2 - 50, m_chart->size().height() - 20);
         m_coordY->setPos(m_chart->size().width()/2 + 50, m_chart->size().height() - 20);
         const auto callouts = m_callouts;
         for (Callout *callout : callouts)
             callout->updateGeometry();
    }
    QGraphicsView::resizeEvent(event);
}

void Chart::mouseMoveEvent(QMouseEvent *event)
{
    m_coordX->setText(QString("X: %1").arg(m_chart->mapToValue(event->pos()).x()));
    m_coordY->setText(QString("Y: %1").arg(m_chart->mapToValue(event->pos()).y()));
    QGraphicsView::mouseMoveEvent(event);
}

void Chart::tooltip(QPointF point, bool state)
{
    if (m_chart == NULL)
        return;
    if (m_tooltip == NULL)
        m_tooltip = new Callout(m_chart);

    if (state) {
        m_tooltip->setText(QString("X: %1 \nY: %2 ").arg(point.x()).arg(point.y()));
        m_tooltip->setAnchor(point);
        m_tooltip->setZValue(11);
        m_tooltip->updateGeometry();
        m_tooltip->show();
    } else {
        m_tooltip->hide();
    }
}


void Chart::keepCallout()
{
    m_callouts.append(m_tooltip);
    m_tooltip = new Callout(m_chart);
}